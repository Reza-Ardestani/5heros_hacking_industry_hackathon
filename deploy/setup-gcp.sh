#!/usr/bin/env bash
# One-time Google Cloud setup for .github/workflows/deploy.yml. Safe to re-run.
# Usage: PROJECT_ID=my-project REGION=us-central1 bash deploy/setup-gcp.sh
# Prerequisites: `gcloud auth login`, a project with billing enabled.
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID}"
REGION="${REGION:-us-central1}"
REPO="${GITHUB_REPO:-Reza-Ardestani/5heros_hacking_industry_hackathon}"
DEPLOY_SA="bb-deployer@$PROJECT_ID.iam.gserviceaccount.com"
RUNTIME_SA="bb-runtime@$PROJECT_ID.iam.gserviceaccount.com"
POOL=github
PROVIDER=github

gcloud config set project "$PROJECT_ID"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format 'value(projectNumber)')

gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com iamcredentials.googleapis.com sts.googleapis.com

gcloud artifacts repositories describe bottleneck-busters --location "$REGION" >/dev/null 2>&1 ||
  gcloud artifacts repositories create bottleneck-busters --location "$REGION" \
    --repository-format docker --description "Bottleneck Busters images"
# Keep storage cost near zero: retain only the 10 newest images.
cat > /tmp/bb-cleanup.json <<'JSON'
[{"name": "keep-recent", "action": {"type": "Keep"}, "mostRecentVersions": {"keepCount": 10}},
 {"name": "delete-rest", "action": {"type": "Delete"}, "condition": {"tagState": "any"}}]
JSON
gcloud artifacts repositories set-cleanup-policies bottleneck-busters --location "$REGION" \
  --policy /tmp/bb-cleanup.json --no-dry-run

for sa in bb-deployer bb-runtime; do
  gcloud iam service-accounts describe "$sa@$PROJECT_ID.iam.gserviceaccount.com" >/dev/null 2>&1 ||
    gcloud iam service-accounts create "$sa"
done

# Shared site password, kept in Secret Manager (never in GitHub).
if ! gcloud secrets describe bb-auth-password >/dev/null 2>&1; then
  read -rsp "Choose the site password (username is 'bottleneck'): " password; echo
  printf '%s' "$password" | gcloud secrets create bb-auth-password --data-file=-
fi
gcloud secrets add-iam-policy-binding bb-auth-password \
  --member "serviceAccount:$RUNTIME_SA" --role roles/secretmanager.secretAccessor >/dev/null

for role in roles/run.admin roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member "serviceAccount:$DEPLOY_SA" --role "$role" --condition None >/dev/null
done
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --member "serviceAccount:$DEPLOY_SA" --role roles/iam.serviceAccountUser >/dev/null

# Keyless GitHub Actions auth, limited to this one repository.
gcloud iam workload-identity-pools describe "$POOL" --location global >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools create "$POOL" --location global --display-name "GitHub Actions"
gcloud iam workload-identity-pools providers describe "$PROVIDER" --location global \
  --workload-identity-pool "$POOL" >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" --location global \
    --workload-identity-pool "$POOL" --issuer-uri https://token.actions.githubusercontent.com \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --attribute-condition "assertion.repository == '$REPO'"
gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/attribute.repository/$REPO" >/dev/null

cat <<EOF

Done. Add these as GitHub repository *variables* (Settings > Secrets and variables >
Actions > Variables) on https://github.com/$REPO :

  GCP_PROJECT_ID    $PROJECT_ID
  GCP_REGION        $REGION
  GCP_WIF_PROVIDER  projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER
  GCP_DEPLOY_SA     $DEPLOY_SA

Then push any branch. Change the password later with:
  printf '%s' 'new-password' | gcloud secrets versions add bb-auth-password --data-file=-
  (new instances pick it up; force it with a redeploy)
EOF

# Plan

Branch from current origin/main. Add a pure score projection for the actual forecast model; expose it through the existing shared prediction service. Update the prediction panel and assistant without changing automatic selection or training windows.

Extract the existing progress presentation into a shared component. Track submission and polling errors separately. Give active and failed status precedence over the empty state in Compare and study.

Add focused regression tests for model association, fallback, missing evidence, assistant wording and UI job transitions. Run backend checks and the frontend production build. Record results in progress; no production deployment is part of this fix.

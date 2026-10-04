# DES-BB-UI-001 — Evidence-first planning workspace

User authorized shared design tokens October 3, 2026. Scope: a reusable visual
foundation and a reviewable gallery, applied to the existing React web app.
[Stories US-BB-001](../../user_stories/planning.md),
[journey UJ-BB-001](../../user_journeys/planner.md),
[owning MVP spec](../../../specs/features/phase-1-hackathon-mvp/requirements.md).

## Why this direction

Users are hypothesized to be transport engineers and budget reviewers making
costly, explainable decisions. Light surfaces keep dense comparisons readable;
navy gives the workspace a stable navigation frame. Teal emphasizes actions and
selection. Color is secondary to source labels, units, constraints, and reasons.
DM Sans and Space Grotesk preserve the app's existing direction; system fonts keep
the interface usable if the optional font download is unavailable.

The organizer's rubric rewards an input-to-decision loop, improvement against a
baseline, industry relevance, working architecture, and a clear demo. This visual
system helps expose that evidence. It does not create those capabilities or
guarantee a win. The four-step walkthrough remains the primary information hierarchy:
problem, intervention, simulation, recommendation.

## Presentation rules

1. Show the decision question before configuration. One primary action per step.
2. Put baseline, candidate, units, and comparison conditions together. Use tabular
   numerals for changing metrics; labels and axis units remain visible.
3. Distinguish observed, modeled, assumed, missing, and unknown data with words and
   visual treatment. Show timestamps and provenance next to the relevant value.
4. Expose constraints and rejected alternatives beside a recommendation. Do not
   make a rejected option invisible or present simulated benefit as measured savings.
5. Reserve red for missing evidence, invalid input, and rejected constraints;
   reserve amber for assumptions or caution. Green observed data still needs
   qualification for location, freshness, interval, and observation method.
6. Use a 4px spacing scale, restrained borders/shadows, and 40px primary controls.
   Provide visible keyboard focus; honor reduced motion. No decorative animation
   competes with the actual agent/tool trace.

## Accessibility boundary

The generator checks named normal-text pairs at 4.5:1 and named focus/control/chart
pairs at 3:1 against their specified backgrounds, following
[W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
and [non-text contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).
State labels accompany color, consistent with
[use-of-color guidance](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).
These are scoped checks, not a whole-application accessibility certification.

## Canonical artifacts

[Token source](../../../frontend/src/design-tokens/tokens.json),
[usage](../../../frontend/src/design-tokens/README.md),
[visual gallery](preview.html). Runtime behavior stays in existing frontend
components; domain rules and simulation behavior are unchanged by the visual system.

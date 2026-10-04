# Bottleneck Busters design tokens

The visual direction is a civic planning studio: a desktop workspace where a
transport engineer can inspect evidence, compare alternatives, and explain a decision.
The palette extends the existing React app; teammates share named decisions rather
than inventing a new shade for each screen. It is a design choice, not a claim of
customer validation or a guaranteed judging outcome.

## Files and use

- `tokens.json`: source of truth, grouped JSON strings. This is a project format,
  not a claim of compliance with a particular token interchange standard.
- `tokens.css`: generated `--bb-*` CSS custom properties, imported by `style.css`.
- `contrast-report.json`: generated measurements for the specified color pairs.
- [Visual gallery](../../../docs/design/design-system/preview.html).
- [Design rationale and usage rules](../../../docs/design/design-system/design.md).

From `frontend/`, run `npm run tokens:build` after changing the JSON. `npm run build`
regenerates the CSS and contrast report automatically. No additional package needed.

```css
.decision-card {
  color: var(--bb-color-ink);
  background: var(--bb-color-surface);
  border-radius: var(--bb-radius-panel);
  padding: var(--bb-space-6);
}
```

## Meaning stays consistent

| Token family | Meaning | Required companion |
|---|---|---|
| Brand teal | Primary action, selection | Action label or selected state |
| Observed green | Measurements / source observations | Source, date, units, method |
| Modeled blue | Simulation or prediction | Model, inputs, assumptions |
| Assumed amber | User-entered or illustrative value | Editable assumption label |
| Missing red | Required evidence unavailable / failed validation | Missing field and next step |
| Neutral | Unknown / not yet assessed | Explicit unknown label |

Observed does not mean valid for every decision; modeled does not mean field-proven.
Eligibility uses explicit “Within constraints” or “Rejected” labels and reasons.
Do not rely on color alone. Chart series use labels and, where needed, dashes or
markers; baseline/candidate/revision/capacity colors do not encode truth or approval.

## Adoption scope

The app now consumes shared base typography, surface/text, navigation colors,
primary/secondary controls, evidence badges, and focus/motion tokens. Existing
specialized charts and feature CSS still contain literals; this is a foundation,
not a completed app-wide design migration. Font stacks retain system fallbacks.
Token pair checks do not establish whole-app WCAG compliance.

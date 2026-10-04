# PowerPoint template

Deliverable: [PowerPoint template](Bottleneck_Busters_Presentation_Template.pptx),
tracked with its [recorded evidence](evidence/SOURCE.json). The rendered export is
also in ignored output/presentation/ and copied into Documents as
`Bottleneck_Busters_Presentation_Template.pptx`.
Ten editable slides: eight for a five-minute pitch, two Q&A/preparation appendix
slides. Speaker notes contain timing, demo cues, evidence sources and replacements.

Use the shared frontend design tokens. The deck uses installed Liberation Sans
for dependable rendering, with the product's navy/teal and evidence colors.
Tables, chart data and architecture/decision diagrams remain native editable
PowerPoint objects. Text remains editable. No image-only slide exports.

## Before presenting

Replace bracketed placeholders on the preparation appendix and in notes with the
final live/backup URLs, exact run ID, consented interview evidence and organizer
approval if received. Customer validation, willingness to pay and resource-provider
integration remain open. No quote, customer or approval has been invented.

Slide seven contains a **recorded** completed study, not a current live result:
run `1099e73c93b943598aedbfe7bbc018e1`, retrieved October 3 at 5:24 PM MDT. The
full unchanged API report and endpoint/time/SHA256 are under
[evidence/](evidence/SOURCE.json). It models a synthetic three-junction corridor
standing in for Deerfoot/Glenmore, an interchange that this corridor geometry does
not faithfully represent. Six percent modeled improvement is not a field saving.
Replace it with a properly scoped final rehearsed result.

The [new organizer delta](../../../organizer_docs/discord/updates-2026-10-03-evening.md)
records optional starter/ElevenLabs use and a rejection of fictitious columns added
to real datasets. Keep raw observed evidence, derived features and assumptions
separate. Labeled simulator assumptions and custom-case approval still need
organizer clarification; do not claim verified eligibility.

## Rebuild

The source is `build_template.mjs`. Use the bundled runtime resolved with
`load_workspace_dependencies`. Copy this source into a private build directory,
link that directory's `node_modules` to the supplied Node packages, and set
`RUNTIME_NODE_MODULES` plus `RUNTIME_NODE`. The source reads the frontend tokens and
uses the presentations skill's first-party finalizer. Export to a new filename
for each revision because the finalizer preserves existing outputs. Render and
visually inspect every slide before delivery.

No installed desktop LibreOffice is needed. If a later export requires
LibreOffice, use only the bundled executable:
`/Users/reza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/MacOS/soffice`.

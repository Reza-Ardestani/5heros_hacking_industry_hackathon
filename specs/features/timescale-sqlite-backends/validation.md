# Validation contract

- Unit/SQLite: journal transaction rollback, existing-file snapshot, source UUID
  reuse, default mode, configuration rejection, fallback status, retry timing,
  credential redaction. Preserve exact downloaded source/City timestamp values.
- Real Timescale: exercise the same Store contract on both backends, including
  collector, saved forecast IDs, simulation history, measurements, estimates,
  and source/checkpoint ownership. Verify catalog hypertable metadata.
- Faults: stop/start database while local data changes; new Store during outage;
  remote commit before local acknowledgement; batch failure; shared-file writers;
  distinct source rejection; recreate destination; replace container using volume.
- Regression: full pytest suite; Ruff on affected Python; frontend focused test,
  TypeScript/Vite build; authored Markdown links; exactly four spec files.

Record actual results in progress.md. A PostgreSQL-only test is not Timescale
acceptance. A skipped integration suite, mocked failure test, or image build
alone does not prove persistence or recovery. Preserve sources and existing data;
run destructive fault probes only against disposable test containers/databases.

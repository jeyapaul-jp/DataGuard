# Design

## Context

See proposal.md — Why. DataGuard is a greenfield Python CLI tool (Python 3.9+, pip-installable). No existing codebase to integrate with; no database schema to migrate. The PRD is finalized at `_bmad-output/planning-artifacts/prds/prd-test_project-2026-09-28/prd.md`.

Key constraints from the PRD:
- 1 engineer, 1 week target
- Must run on Linux, macOS, and Windows
- No cloud-provider SDK required for on-prem deployments
- Credentials via environment variables only (no secrets manager in v1)

## Goals / Non-Goals

**Goals:**
- Package structure that separates connector, check-type, execution, and results layers so new connectors and check types can be added without redesigning core
- Simple, testable design — each check type is a pure function (inputs → Result Record)
- Single CLI entry point (`dataGuard run`) with clear error reporting

**Non-Goals:**
- Plugin system or dynamic loading — extensibility is a code-level concern, not a runtime one
- Async or parallel check execution — sequential execution is sufficient for v1
- Type-safe connector configuration via generated models — plain dataclass or dict is fine for v1

## Decisions

### D1: Python packaging — Click CLI + setuptools entry point
**Decision**: Use Click for CLI argument parsing; expose `dataGuard` as a console_scripts entry point in pyproject.toml.
**Why over argparse**: Click handles subcommand structure (`run`, future commands), auto-generates `--help`, and has better error messages. Argparse would work but requires more boilerplate for subcommands.
**Alternative considered**: Typer (Click wrapper with type hints) — rejected because it adds a dependency and its auto-generated help is less controllable for v1.

### D2: Connector abstraction — abstract base class per connector
**Decision**: Define a `BaseConnector` abstract class with a `read(query_or_path, params) → DataFrame` method. Each connector (SQL, CSV, Parquet, JSON, Snowflake, Databricks) implements it. Check types receive DataFrames — they have no connector knowledge.
**Why**: Keeps check logic connector-agnostic. A Row Count check does not need to know whether it's counting a Parquet file or a Snowflake table.
**Alternative considered**: Duck typing with no base class — rejected because type errors surface at runtime in the middle of a check rather than at connector initialization.

### D3: Check types — pure functions, not classes
**Decision**: Each check type is a module-level function: `run_check(config: CheckConfig, source_df: DataFrame, target_df: DataFrame | None) → CheckResult`. The execution engine calls connectors, then passes DataFrames to the check function.
**Why**: Pure functions are easy to unit test — no mocking of connectors needed. Classes add boilerplate without benefit for v1's sequential model.

### D4: Results output — writer abstraction with two implementations
**Decision**: Define a `ResultsWriter` protocol with `write(result: CheckResult, sample_rows: DataFrame | None)`. Two implementations: `DatabaseWriter` (SQLAlchemy for DB table writes) and `FileWriter` (pandas to CSV/JSON). Writer is instantiated once per run from the output config.
**Why**: Isolates output format from check logic. Swapping from file to DB output requires only a config change.

### D5: Config parsing — Pydantic v2 models
**Decision**: Parse YAML/JSON config into Pydantic v2 models. Validation errors surface as human-readable messages with field names.
**Why over plain dicts**: Field-level validation (required fields, type coercion) is free. Error messages name the offending field automatically.
**Alternative considered**: cattrs — less mature ecosystem, less familiar to most Python engineers.

### D6: Databricks connector — databricks-sql-connector (not Spark)
**Decision**: Use the `databricks-sql-connector` Python package to connect to Databricks SQL Warehouses via HTTP path and access token. This does not require a Spark runtime.
**Why**: The PRD assumption (§4.4) is confirmed: SQL Warehouse connection, not Spark. The `databricks-sql-connector` is lightweight and pip-installable.

### D7: Optional cloud dependencies — extras in pyproject.toml
**Decision**: Cloud storage support (S3, Azure Blob, GCS) is exposed as pip extras (`dataguard[s3]`, `dataguard[azure]`, `dataguard[gcs]`). Core install has no cloud SDK dependency.
**Why**: Satisfies the PRD NFR that on-prem deployments require no cloud-provider SDK. Missing optional dependency → clear `ImportError` with install hint at connector init time.

## Risks / Trade-offs

- **Large dataset performance**: Pandas DataFrames load full datasets into memory. For checks on tables with millions of rows, memory use may be significant. Mitigation: push aggregation queries down to the database (count, sum, avg) and only fetch sample rows when needed — avoid `SELECT *` for aggregate checks.
- **Sequential execution**: Checks run one at a time. A run with many slow checks will take proportionally longer. Mitigation: acceptable for v1; parallel execution is a v2 candidate once usage patterns are understood.
- **Config credential exposure**: Inline credentials in YAML files are a security risk if files are version-controlled. Mitigation: document environment variable usage prominently; do not log credential values in error messages.
- **Windows path handling**: File connector paths must handle both Unix and Windows separators. Mitigation: use `pathlib.Path` throughout; test on Windows explicitly.

## Migration Plan

Greenfield project — no migration needed. Deployment is `pip install dataguard`. Rollback is `pip uninstall dataguard`.

## Open Questions

1. Should `dataGuard run` accept multiple `--config` files in one invocation (running checks from several files as a single combined run)? Not needed for v1 but affects the CLI interface design.
2. Is there a preferred database dialect for the Results Store for the first adopter teams? This determines which SQLAlchemy dialect to test most thoroughly.

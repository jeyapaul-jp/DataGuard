# Proposal

## Why

Data engineers and QA testers currently validate ETL pipelines by hand — querying source and target systems separately, comparing counts, and spot-checking nulls. This is slow, inconsistent, produces no audit trail, and misses edge cases until they reach downstream consumers. DataGuard automates these checks with a config-driven CLI tool any internal team can adopt without writing code.

## What Changes

- **New**: `dataGuard run --config <path>` CLI command that executes all checks defined in a YAML or JSON config file against source and target data stores
- **New**: Config File format (YAML/JSON) for defining per-check validation rules with connection details, check type, and thresholds — no application code required
- **New**: Five check types: Row Count, Duplicate Detection, Null Threshold, Referential Integrity, Reconciliation
- **New**: Six connectors: SQL (JDBC/ODBC), CSV, Parquet, JSON, Snowflake, Databricks — cloud and on-prem
- **New**: Structured results written to a configurable Results Store (database table or CSV/JSON file), with sample rows on failure for applicable check types
- **New**: Check-level error isolation — connection failures produce ERROR status and the run continues; intentionally disabled checks produce SKIP status
- **New**: Non-zero CLI exit code when any check is FAIL or ERROR; run summary printed to stdout

## Capabilities

### New Capabilities

- `dataguard/config`: Config File parsing and validation — YAML/JSON format, per-check block structure, shared connection references, credential handling via environment variables
- `dataguard/checks`: Five check types (Row Count, Duplicate Detection, Null Threshold, Referential Integrity, Reconciliation) with pass/fail logic, sample rows on failure, and configurable thresholds
- `dataguard/connectors`: Six connector adapters (SQL/JDBC, CSV, Parquet, JSON, Snowflake, Databricks) with connection parameter handling and connection-failure ERROR reporting
- `dataguard/execution`: CLI execution engine — run command, check ordering, ERROR/SKIP status semantics, run summary output, exit code behavior
- `dataguard/results`: Results Store output — default and configurable schema, database table and file (CSV/JSON) targets, append-by-default behavior, sample row linkage

### Modified Capabilities

*(none — this is a greenfield v1)*

## Impact

- **New Python package**: `dataguard` — pip-installable, Python 3.9+, runs on Linux/macOS/Windows
- **New dependencies**: connector libraries (SQLAlchemy or equivalent for SQL/JDBC, snowflake-connector-python, databricks-sql-connector, pandas/pyarrow for file connectors)
- **No existing code affected**: greenfield project, no current internal tooling to displace
- **Results Store consumers**: any BI tool (Grafana, Tableau, Power BI) that can query the configured database table or read the output CSV/JSON file

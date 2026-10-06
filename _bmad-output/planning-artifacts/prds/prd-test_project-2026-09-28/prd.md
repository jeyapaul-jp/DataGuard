---
title: DataGuard — Data Validation Framework
status: final
created: 2026-09-28
updated: 2026-09-28
---

# PRD: DataGuard — Data Validation Framework

## 0. Document Purpose

This PRD is for the engineering team building DataGuard and any downstream workflow owners (architecture, sprint planning). It defines what DataGuard must do — not how to build it. Vocabulary is anchored in §3 Glossary; all FRs, user journeys, and success metrics use those terms verbatim. The finalized product brief lives at `_bmad-output/planning-artifacts/briefs/brief-test_project-2026-09-28/brief.md` — this PRD supersedes it for implementation purposes.

---

## 1. Vision

Data pipelines fail silently. Counts drift, duplicates slip through, nulls reach consumers, and reconciliation gaps go undetected until they surface as production incidents or wrong reports. Today, testers validate pipelines by hand — querying source and target separately, comparing counts, spot-checking nulls. This is slow, inconsistent, and unscalable.

DataGuard automates this. Engineers define validation rules in a Config File; DataGuard connects to source and target systems, runs the checks, and writes structured results to a Results Store — what took hours of manual work runs in minutes, every time, with a full audit trail. No custom code. No proprietary UI. No managed service dependency. The framework is a standalone CLI tool any internal team can adopt.

V1 is scoped to a single engineer in one week. The measure of success is simple: a team onboards a new pipeline in under an hour and runs a full validation suite without touching it again. The long-term bet is that teams stop treating data validation as a manual QA step and start treating it as a first-class part of every pipeline run.

---

## 2. Target User

### 2.1 Jobs To Be Done

- Know whether data loaded from source to target completely and correctly, without running queries by hand.
- Catch data quality problems (nulls, duplicates, count mismatches, referential breaks) before downstream consumers are affected.
- Have an audit trail — timestamped pass/fail results per check, per run — without building one themselves.
- Onboard a new pipeline to automated validation without writing application code.
- Trust that if a check couldn't run (connection failure), they're told — not silently misled by a missing result.

### 2.2 Non-Users (v1)

- Data consumers and analysts — they benefit indirectly from fewer incidents, but do not interact with DataGuard directly.
- Teams that need real-time or streaming validation.
- Teams that need auto-remediation or alerting built into the tool — results output is DataGuard's boundary.

### 2.3 Key User Journeys

- **UJ-1.** Ravi, a data engineer, writes a DataGuard config for a new ETL pipeline, runs it from the CLI, and sees pass/fail results appear in his team's existing Grafana dashboard by the time he grabs coffee.
- **UJ-2.** Priya, a QA tester, runs DataGuard as part of a pre-release check. Two checks fail — count mismatch and a null threshold breach. She reads the sample rows in the results store, identifies the bad records, and escalates with the row-level evidence in hand.
- **UJ-3.** James onboards a second pipeline team. He copies the config from the first pipeline, adjusts connection details and check parameters, and runs DataGuard. The new pipeline is validated in under an hour — no code written. [ASSUMPTION: Config is portable across teams with minimal edits to connection details.]

---

## 3. Glossary

- **Validation Run** — a single execution of DataGuard triggered via CLI against one Config File. A run contains one or more Checks.
- **Check** — a single validation rule defined in the Config File. Has a Check Type, a Source, a Target, and type-specific parameters. The atomic unit of DataGuard.
- **Check Type** — the category of validation logic applied to a check. V1 types: Row Count, Duplicate Detection, Null Threshold, Referential Integrity, Reconciliation.
- **Source** — the originating data store for a check (the "from" side of an ETL).
- **Target** — the destination data store for a check (the "to" side of an ETL).
- **Connector** — a DataGuard adapter that reads from or queries a specific data store type. V1 connectors: SQL, CSV, Parquet, JSON, Snowflake, Databricks.
- **Results Store** — the output destination where check results are written after a run. Either a database table or a file (CSV or JSON).
- **Result Record** — one row written to the Results Store per check per run. Contains at minimum: run ID, check name, check type, status (PASS / FAIL / SKIP / ERROR), actual value, expected value or threshold, and timestamp.
- **Sample Rows** — a subset of rows from the source or target that illustrate a failed check, written alongside the Result Record for diagnostic use.
- **Config File** — a YAML or JSON file that defines all checks for a run, their connection details, and output configuration.
- **SKIP** — a check status indicating the check was intentionally not executed: either `enabled: false` in the Config File, or excluded via `--skip <check-name>` CLI flag. Distinct from ERROR (runtime or connection failure). A SKIP still produces a Result Record.

---

## 4. Features

### 4.1 Configuration

**Description:** Engineers define all checks in a single Config File. Each check is a self-contained block specifying its type, source connection, target connection, and check-specific parameters. There is no global pipeline concept — the unit of configuration is the individual check. A Config File may contain one check or many. Connection details (host, credentials, format) are specified per check and may be repeated across checks or extracted to shared references. [ASSUMPTION: Credentials may be supplied inline in the config or via environment variables; secrets management beyond environment variables is out of v1.]

**Functional Requirements:**

#### FR-1: Config File Format

Engineer can define checks in a YAML or JSON Config File. DataGuard accepts both formats interchangeably.

**Consequences (testable):**
- A valid YAML Config File and an equivalent JSON Config File produce identical check execution behavior.
- DataGuard returns a parse error with the offending line number if the Config File is malformed.

#### FR-2: Per-Check Configuration

Each check block in the Config File specifies: a unique check name, a check type, a source connection, a target connection (where applicable), and check-type-specific parameters.

**Consequences (testable):**
- Two checks of different types coexist in one Config File and execute independently.
- A missing required field (e.g. check type, source) causes DataGuard to reject the Config File at parse time with a descriptive error identifying the offending check by name.

#### FR-3: Shared Connection References

Engineer can define a named connection block once in the Config File and reference it by name in multiple checks, avoiding duplication.

**Consequences (testable):**
- A config with three checks sharing one connection block executes identically to a config with three checks each with the connection inlined.

---

### 4.2 CLI Execution and Error Handling

**Description:** DataGuard runs via CLI. A single command accepts the Config File path and executes all checks in it. Two distinct non-success statuses apply: ERROR (DataGuard attempted the check but failed — connection refused, credentials invalid, query error) and SKIP (the check was intentionally excluded via config or CLI flag and never attempted). Connection failures produce ERROR, not SKIP; they do not abort the run — execution continues with remaining checks. At completion, DataGuard prints a summary to stdout and exits with a non-zero exit code if any check is FAIL or ERROR. SKIP is not a failure condition.

**Functional Requirements:**

#### FR-4: CLI Invocation

Engineer can invoke DataGuard from the command line, passing the Config File path as an argument.

**Consequences (testable):**
- `dataGuard run --config <path>` executes all checks defined in the Config File.
- `dataGuard --help` prints usage.
- DataGuard exits 0 if all checks pass; exits non-zero if any check is FAIL or ERROR.

#### FR-5: Connection Failure Isolation

If DataGuard cannot establish a connection to a check's source or target, that check's status is set to ERROR with a reason, written to the Results Store, and execution continues with the next check. The run does not abort.

**Consequences (testable):**
- A config with 5 checks where check 3 has an unreachable source: checks 1, 2, 4, 5 execute; check 3 is recorded as ERROR; run completes.
- The ERROR Result Record contains the connection error message.
- DataGuard exits non-zero.

#### FR-5b: Intentional Check Skip

Engineer can set `enabled: false` on any check block in the Config File, or pass `--skip <check-name>` at the CLI, to exclude a check from the run. Excluded checks are recorded as SKIP in the Results Store.

**Consequences (testable):**
- A check with `enabled: false` produces a SKIP Result Record and is not executed.
- `--skip <check-name>` at runtime produces the same SKIP result without modifying the Config File.
- DataGuard exits 0 if all executed checks pass and remaining checks are SKIP only.

#### FR-6: Run Summary Output

At the end of each Validation Run, DataGuard prints a summary to stdout: total checks, count by status (PASS / FAIL / SKIP / ERROR), and the path to the Results Store output.

**Consequences (testable):**
- stdout contains check-level status lines and a final summary count.
- The Results Store path is printed regardless of whether any check failed.

---

### 4.3 Check Types

**Description:** V1 supports five check types. Each check produces a Result Record (pass/fail + actual vs. expected values). On failure, Sample Rows are written alongside the Result Record — a configurable number of illustrative rows (default: 5), not a full dump. [ASSUMPTION: Sample row count is configurable per check in the config; default is 5 if not specified.]

**Functional Requirements:**

#### FR-7: Row Count Check

Engineer can configure a check that compares the row count of a source query or table against a target query or table and fails if the delta exceeds a configured threshold (absolute count or percentage).

**Consequences (testable):**
- Source count 1000, target count 950, threshold 1%: check FAILs; Result Record contains source count, target count, delta, threshold.
- Source count 1000, target count 995, threshold 1%: check PASSes.
- On FAIL, Sample Rows are not applicable (count check has no row-level evidence); result contains counts only.

#### FR-8: Duplicate Detection Check

Engineer can configure a check that detects duplicate rows in a source or target dataset, defined by a set of key columns.

**Consequences (testable):**
- Dataset with 3 rows sharing the same key columns: check FAILs; Result Record contains duplicate count; Sample Rows include up to N duplicate rows.
- Dataset with no duplicate keys: check PASSes.

#### FR-9: Null / Blank Threshold Check

Engineer can configure a check that fails if the null or blank rate for a specified column exceeds a configured threshold (percentage).

**Consequences (testable):**
- Column with 15% null rate, threshold 10%: check FAILs; Result Record contains actual null rate, threshold; Sample Rows include up to N rows where the column is null.
- Column with 8% null rate, threshold 10%: check PASSes.

#### FR-10: Referential Integrity Check

Engineer can configure a check that verifies every value in a source column exists in a target reference column (foreign key integrity).

**Consequences (testable):**
- Source column contains values [A, B, C]; target reference contains [A, B]: check FAILs; Result Record contains count of orphaned values; Sample Rows include up to N rows with orphaned values.
- All source values present in target reference: check PASSes.

#### FR-11: Reconciliation Check

Engineer can configure a check that compares an aggregate (sum, count, average — configurable) of a source column against the same aggregate of a target column, failing if the delta exceeds a threshold.

**Consequences (testable):**
- Source sum 1,000,000.00, target sum 999,500.00, threshold 0.1%: check FAILs; Result Record contains source aggregate, target aggregate, delta, threshold.
- Delta within threshold: check PASSes.
- On FAIL, Sample Rows are not applicable (aggregate check); result contains aggregate values only.

---

### 4.4 Connector Support

**Description:** Connectors abstract the source and target system details from check logic. Each check specifies its source and target connector type and connection parameters. V1 supports SQL (generic JDBC/ODBC), CSV, Parquet, JSON, Snowflake, and Databricks. DataGuard runs on cloud and on-prem environments — there is no cloud-only runtime dependency. [ASSUMPTION: Databricks connector uses the Databricks SQL connector or JDBC endpoint, not Spark runtime; confirm with engineering.]

**Functional Requirements:**

#### FR-12: SQL Connector

DataGuard connects to any SQL-compliant database via JDBC/ODBC using host, port, database, and credentials specified in the config.

**Consequences (testable):**
- DataGuard executes a count query against a SQL Server, PostgreSQL, or Oracle source and returns results.
- Connection failure produces an ERROR Result Record with the SQL error message.

#### FR-13: File Connectors (CSV, Parquet, JSON)

DataGuard reads CSV, Parquet, and JSON files from local paths or cloud object storage paths (S3, Azure Blob, GCS) as source or target for any check type.

**Consequences (testable):**
- A count check against a local Parquet file and a Snowflake target executes without error.
- An unreadable or missing file path produces an ERROR Result Record.

#### FR-14: Snowflake Connector

DataGuard connects to Snowflake using account, warehouse, database, schema, and credentials (username/password or key-pair) specified in the config.

**Consequences (testable):**
- DataGuard executes a query against a Snowflake table and returns results.
- Connection failure (invalid credentials, unreachable account) produces an ERROR Result Record with the Snowflake error message.

#### FR-15: Databricks Connector

DataGuard connects to a Databricks SQL warehouse using the JDBC endpoint or Databricks connector SDK, with host, HTTP path, and token specified in the config.

**Consequences (testable):**
- DataGuard executes a query against a Databricks table and returns results.
- Connection failure (invalid token, unreachable warehouse) produces an ERROR Result Record with the Databricks error message.

---

### 4.5 Results Output

**Description:** After each check executes, DataGuard writes one Result Record to the Results Store. The Results Store is either a database table or a file (CSV or JSON), configured in the Config File. The output schema is configurable — engineers specify which fields to include. A default schema is provided and applies when no output schema override is configured. Sample Rows for failed checks are written to the same Results Store as child records linked to the parent Result Record by run ID and check name. [ASSUMPTION: Results Store schema versioning is out of v1; breaking schema changes require teams to reconfigure.]

**Functional Requirements:**

#### FR-16: Default Result Record Schema

DataGuard writes a Result Record containing: run ID (UUID), check name, check type, status (PASS / FAIL / SKIP / ERROR), actual value, expected value or threshold, delta (where applicable), connector types used (source/target), and ISO-8601 timestamp.

**Consequences (testable):**
- After a run, the Results Store contains one row per check with all default fields populated.
- A SKIP record (check not executed due to dependency) and an ERROR record (connection failure) both produce records with appropriate status and reason fields.

#### FR-17: Configurable Output Schema

Engineer can specify in the Config File which fields to include in the Result Record, overriding the default schema. Fields not selected are omitted from output.

**Consequences (testable):**
- Config specifying output fields [check_name, status, timestamp] produces Result Records with only those three columns.
- An invalid field name in the output config produces a parse-time error.

#### FR-18: Sample Rows on Failure

For check types that support sample rows (Duplicate Detection, Null Threshold, Referential Integrity), DataGuard writes up to N sample rows to the Results Store on FAIL, linked to the Result Record by run ID and check name. N is configurable per check; default is 5.

**Consequences (testable):**
- A Null Threshold check that fails writes the Result Record plus up to 5 sample rows containing the null-valued column.
- Configuring `sample_rows: 10` in the check block produces up to 10 sample rows.
- Row Count and Reconciliation checks do not produce sample rows on failure.

#### FR-19: Results Store Targets

Engineer can configure the Results Store as: (a) a database table (SQL-compatible, specified by connection + table name), or (b) a file (CSV or JSON, specified by output path). The Config File specifies the target type and connection/path details.

**Consequences (testable):**
- A run configured with a database Results Store writes records to the named table.
- A run configured with a CSV file Results Store appends records to the named file path across runs (cumulative history); the file is created if it does not exist.
- Engineer can set `overwrite: true` in the output config to replace the file on each run instead of appending.

---

## 5. Non-Goals (Explicit)

- **No UI or dashboard** — DataGuard writes results to a store; visualization is the consuming team's concern.
- **No real-time or streaming validation** — batch ETL only in v1.
- **No alerting or notification** — DataGuard exits with a status code; routing alerts is the consumer's concern.
- **No auto-remediation** — DataGuard detects and reports; it does not fix.
- **No ML-based anomaly detection** — all check thresholds are user-defined.
- **No orchestrator-native integrations** — CLI is the entry point; Airflow operators, Databricks Jobs SDK wrappers, etc. are out of v1.
- **No schema drift detection** — DataGuard validates data, not schema changes. [ASSUMPTION: Flag if this is a v1 blocker.]
- **No column-level profiling** — checks are targeted, not exhaustive scans.
- **No multi-tenancy or access control** — internal tool; no user accounts or permission model.

---

## 6. MVP Scope

### 6.1 In Scope

- Config-driven check definitions (YAML and JSON)
- Check types: Row Count, Duplicate Detection, Null Threshold, Referential Integrity, Reconciliation
- Connectors: SQL (JDBC/ODBC), CSV, Parquet, JSON, Snowflake, Databricks
- Cloud and on-prem execution (no cloud-only runtime dependency)
- Check-level skip on connection failure with ERROR status
- Configurable Results Store (database table or CSV/JSON file)
- Configurable output schema
- Sample rows on failure for applicable check types
- CLI invocation with non-zero exit on failure or error
- Run summary to stdout
- Self-service onboarding documentation

### 6.2 Out of Scope for MVP

- Native UI or dashboard
- Real-time or streaming validation
- Alerting or notification routing
- Auto-remediation
- ML-based anomaly detection
- Orchestrator-native integrations (Airflow, Databricks Jobs SDK) [NOTE FOR PM: High-value v2 candidate — teams will ask for this quickly once CLI adoption grows.]
- Schema drift detection [NOTE FOR PM: Revisit for v2 if teams flag it during v1 onboarding.]
- Column-level profiling
- Secrets management beyond environment variables
- Results Store schema versioning
- Multi-tenancy or access control

---

## 7. Success Metrics

**Primary**

- **SM-1:** Onboarding time — a new team runs their first full validation suite in under 1 hour from a standing start, using only the documentation. Validates FR-1, FR-2, FR-4. Target: confirmed by at least 2 teams within 30 days of release.
- **SM-2:** Check coverage — all 5 check types execute correctly against at least 2 distinct connector type pairs (e.g. SQL → Snowflake, CSV → Databricks). Validates FR-7 through FR-15.
- **SM-3:** Reliability — a Validation Run where one check errors (connection failure) completes the remaining checks and writes results for all. Validates FR-5, FR-6.

**Secondary**

- **SM-4:** Results schema usability — Results Store output is consumable by a standard BI tool (Grafana, Tableau, Power BI) without transformation. Validates FR-16, FR-17.
- **SM-5:** Team adoption — at least 2 internal teams adopt DataGuard within 30 days of release. [ASSUMPTION: This is the primary usability proxy for v1.]

**Counter-metrics (do not optimize)**

- **SM-C1:** Check runtime — do not optimize for speed at the cost of correctness. A check that runs fast but returns wrong sample rows or misreports delta values is worse than a slow correct one.
- **SM-C2:** Config complexity — do not add config options that require reading source code to use. If a config field needs more than one sentence to explain, it is too complex for v1.

---

## 8. Cross-Cutting NFRs

- **Runtime:** DataGuard is implemented in Python. Distribution is via pip-installable package. Python 3.9+ required. [ASSUMPTION: Python is the confirmed runtime — resolved from open question OQ-1.]
- **Performance:** DataGuard must complete a single check against a dataset of up to 10 million rows in under 5 minutes on standard hardware. [ASSUMPTION: 10M row ceiling and 5-minute budget are reasonable for v1 internal ETL pipelines — confirm with engineering.]
- **Reliability:** A check that fails or errors must not affect the execution of other checks in the same run.
- **Observability:** Every check execution produces a Result Record — no silent failures, no missing records.
- **Extensibility:** The connector and check-type layers must be separated in implementation so new connector types and check types can be added without redesigning the core. [NOTE FOR PM: This is a discipline constraint on engineering, not a user-facing requirement.]
- **Portability:** DataGuard must run on Linux, macOS, and Windows. No cloud-provider SDK must be required for on-prem deployments.
- **Documentation:** Self-service onboarding documentation must cover: installation, writing a first config file, connector configuration reference, check type reference, results schema reference, and a worked example end-to-end.

---

## 9. Open Questions

1. How should credentials be handled in the Config File for teams with stricter secrets policies? Environment variable injection covers basic cases — is that sufficient for all v1 teams?
2. Is there a preferred Results Store target for the first adopter teams? Knowing this early shapes which connector to test most rigorously.
3. When a check's expected value (e.g. reconciliation total) is derived dynamically from a query rather than hardcoded, is that in scope for v1 config syntax?

---

## 10. Assumptions Index

- **§4.1 / §2.3** — Credentials are supplied inline in the config or via environment variables; secrets management beyond environment variables is out of v1.
- **§2.3** — Config is portable across teams with minimal edits to connection details (no team-specific framework coupling).
- **§4.3** — Sample row count is configurable per check; default is 5 if not specified.
- **§4.4** — Databricks connector uses the Databricks SQL connector or JDBC endpoint, not Spark runtime — confirm with engineering.
- **§4.5** — Results Store schema versioning is out of v1; breaking schema changes require teams to reconfigure.
- **§5** — Schema drift detection is not a v1 blocker — flag if wrong.
- **§7 / §8** — 10M row ceiling and 5-minute performance budget are reasonable for internal ETL pipelines — confirm with engineering.
- **§7** — Adoption by 2 internal teams within 30 days is the primary usability proxy for v1.
- **Brief** — No existing internal tooling is in use; DataGuard should replace rather than co-exist with informal scripts.
- **Brief** — No dedicated data platform team manages a centralized catalog. Teams adopt tooling independently.
- **§8** — Python is the confirmed runtime (resolved OQ-1); pip-installable, Python 3.9+.
- **§4.5** — File Results Store default behavior is append across runs; `overwrite: true` config flag enables per-run replacement (resolved OQ-4).

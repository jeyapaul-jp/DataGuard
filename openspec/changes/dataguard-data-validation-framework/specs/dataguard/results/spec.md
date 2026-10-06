# Spec Delta

## Purpose

Defines the Results Store output — the structured records DataGuard writes after each check, the default and configurable schema, and the supported output targets (database table or file).

## ADDED Requirements

### Requirement: Default Result Record Schema
DataGuard SHALL write one Result Record to the Results Store per check per Validation Run. The default schema SHALL include: run ID (UUID), check name, check type, status (PASS / FAIL / SKIP / ERROR), actual value, expected value or threshold, delta where applicable, source connector type, target connector type, and ISO-8601 timestamp.

#### Scenario: Completed run produces one Result Record per check
- **WHEN** a Validation Run with 4 checks completes
- **THEN** the Results Store contains exactly 4 Result Records, one per check, each with all default schema fields populated

#### Scenario: SKIP and ERROR records include status and reason
- **WHEN** a check is recorded as SKIP or ERROR
- **THEN** its Result Record contains the appropriate status and a reason field describing why it was skipped or what error occurred

### Requirement: Configurable Output Schema
Engineers SHALL be able to specify which Result Record fields to include via an `output_fields` list in the Config File's output section. Fields not listed SHALL be omitted from output. An invalid field name SHALL be rejected at parse time.

#### Scenario: Custom field list produces records with only specified fields
- **WHEN** the config specifies `output_fields: [check_name, status, timestamp]`
- **THEN** each Result Record contains only those three columns

#### Scenario: Invalid field name is rejected at parse time
- **WHEN** `output_fields` contains a name that is not a valid Result Record field
- **THEN** DataGuard exits with a non-zero code before executing any checks

### Requirement: Database Table Results Store
Engineers SHALL be able to configure the Results Store as a SQL-compatible database table by specifying a connection and table name in the Config File.

#### Scenario: Results are written to the named database table
- **WHEN** the output config specifies a database connection and table name
- **THEN** DataGuard writes all Result Records for the run to that table after checks complete

### Requirement: File Results Store
Engineers SHALL be able to configure the Results Store as a CSV or JSON file by specifying an output path in the Config File. File Results Stores SHALL append records across runs by default. Engineers SHALL be able to set `overwrite: true` in the output config to replace the file on each run.

#### Scenario: File Results Store appends across runs by default
- **WHEN** a run completes and the output file already exists
- **THEN** Result Records are appended to the existing file, preserving prior run history

#### Scenario: File is created if it does not exist
- **WHEN** a run completes and the configured output file path does not yet exist
- **THEN** DataGuard creates the file and writes the Result Records for that run

#### Scenario: Overwrite mode replaces the file on each run
- **WHEN** the output config sets `overwrite: true` and the output file already exists
- **THEN** the file is replaced with only the Result Records from the current run

### Requirement: Sample Row Linkage
Sample rows written on check failure SHALL be linked to their parent Result Record by run ID and check name, enabling consumers to join sample rows to their corresponding Result Record.

#### Scenario: Sample rows share run ID and check name with parent record
- **WHEN** a Null Threshold check fails and sample rows are written
- **THEN** each sample row record contains the same run_id and check_name as the parent Result Record

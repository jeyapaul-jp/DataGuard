# Spec Delta

## Purpose

Defines the CLI interface, check execution semantics, status values (PASS, FAIL, SKIP, ERROR), run summary output, and exit code behavior for a DataGuard Validation Run.

## ADDED Requirements

### Requirement: CLI Invocation
The system SHALL provide a `dataGuard run` command that accepts a `--config <path>` argument pointing to a Config File and executes all checks defined in it.

#### Scenario: Valid config executes all checks
- **WHEN** `dataGuard run --config <path>` is invoked with a valid Config File
- **THEN** DataGuard executes every enabled check in the file and writes results to the configured Results Store

#### Scenario: Help flag prints usage
- **WHEN** `dataGuard --help` is invoked
- **THEN** DataGuard prints usage information and exits with code 0

#### Scenario: Missing config path argument is reported
- **WHEN** `dataGuard run` is invoked without `--config`
- **THEN** DataGuard exits with a non-zero code and prints a usage error

### Requirement: Connection Failure Isolation
When DataGuard cannot establish a connection to a check's source or target, that check's status SHALL be set to ERROR with the connection error message, written to the Results Store, and execution SHALL continue with the remaining checks. A connection failure SHALL NOT abort the run.

#### Scenario: Connection failure in one check does not abort the run
- **WHEN** a run contains 5 checks and check 3 has an unreachable source
- **THEN** checks 1, 2, 4, and 5 execute; check 3 is recorded as ERROR with the connection error; the run completes

### Requirement: Intentional Check Skip
A check SHALL be excluded from execution — and recorded as SKIP — when the check's config block sets `enabled: false`, or when the check name is passed via `--skip <check-name>` at the CLI.

#### Scenario: Disabled check is recorded as SKIP without executing
- **WHEN** a check block sets `enabled: false`
- **THEN** the check is recorded as SKIP in the Results Store and its validation logic is not executed

#### Scenario: CLI skip flag excludes a check at runtime
- **WHEN** `dataGuard run --config <path> --skip <check-name>` is invoked
- **THEN** the named check is recorded as SKIP without modifying the Config File; all other checks execute normally

### Requirement: Run Summary Output
At the end of every Validation Run, DataGuard SHALL print a summary to stdout listing: total checks, count by status (PASS / FAIL / SKIP / ERROR), and the resolved path to the Results Store output.

#### Scenario: Summary is printed regardless of check outcomes
- **WHEN** a Validation Run completes — whether all checks pass, some fail, or some error
- **THEN** stdout contains per-check status lines and a final summary count, followed by the Results Store path

### Requirement: Exit Code Behavior
DataGuard SHALL exit with code 0 when all executed checks have status PASS or SKIP. DataGuard SHALL exit with a non-zero code when any executed check has status FAIL or ERROR.

#### Scenario: All passing checks produce exit code 0
- **WHEN** all executed checks pass (SKIP checks are excluded from evaluation)
- **THEN** DataGuard exits with code 0

#### Scenario: Any failed or errored check produces non-zero exit code
- **WHEN** at least one check has status FAIL or ERROR
- **THEN** DataGuard exits with a non-zero code

#### Scenario: A run of only SKIP checks produces exit code 0
- **WHEN** all checks in the Config File are excluded via `enabled: false` or `--skip`
- **THEN** DataGuard exits with code 0 and the summary reports 0 executed checks

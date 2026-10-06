# Spec Delta

## Purpose

Defines the five check types DataGuard executes, their pass/fail logic, configurable thresholds, and the sample-row evidence written alongside failing checks.

## ADDED Requirements

### Requirement: Row Count Check
The system SHALL support a Row Count check that compares the row count of a source dataset against a target dataset and fails if the absolute or percentage delta exceeds a configured threshold.

#### Scenario: Count delta within threshold passes
- **WHEN** source row count is 1000, target row count is 998, and threshold is 1%
- **THEN** the check status is PASS and the Result Record contains source count, target count, and delta

#### Scenario: Count delta exceeds threshold fails
- **WHEN** source row count is 1000, target row count is 950, and threshold is 1%
- **THEN** the check status is FAIL and the Result Record contains source count, target count, delta, and threshold

#### Scenario: Row Count check produces no sample rows on failure
- **WHEN** a Row Count check fails
- **THEN** no sample rows are written; the Result Record contains aggregate counts only

### Requirement: Duplicate Detection Check
The system SHALL support a Duplicate Detection check that identifies rows in a source or target dataset sharing the same values across a configured set of key columns.

#### Scenario: Dataset with no duplicates passes
- **WHEN** all rows in the dataset have unique values across the configured key columns
- **THEN** the check status is PASS

#### Scenario: Dataset with duplicates fails and returns sample rows
- **WHEN** two or more rows share identical key-column values
- **THEN** the check status is FAIL; the Result Record contains the duplicate row count; and up to N sample duplicate rows are written, where N is the configured sample size (default 5)

### Requirement: Null Threshold Check
The system SHALL support a Null Threshold check that fails if the null or blank rate for a specified column exceeds a configured percentage threshold.

#### Scenario: Null rate within threshold passes
- **WHEN** a column has an 8% null rate and the threshold is 10%
- **THEN** the check status is PASS

#### Scenario: Null rate exceeds threshold fails and returns sample rows
- **WHEN** a column has a 15% null rate and the threshold is 10%
- **THEN** the check status is FAIL; the Result Record contains actual null rate and threshold; and up to N sample rows where the column is null are written

### Requirement: Referential Integrity Check
The system SHALL support a Referential Integrity check that verifies every value in a specified source column exists in a specified target reference column.

#### Scenario: All source values present in target reference passes
- **WHEN** every distinct value in the source column exists in the target reference column
- **THEN** the check status is PASS

#### Scenario: Orphaned source values fail and return sample rows
- **WHEN** one or more source column values do not exist in the target reference column
- **THEN** the check status is FAIL; the Result Record contains the count of orphaned values; and up to N sample rows with orphaned values are written

### Requirement: Reconciliation Check
The system SHALL support a Reconciliation check that compares a configured aggregate (sum, count, or average) of a source column against the same aggregate of a target column, failing if the delta exceeds a configured threshold.

#### Scenario: Aggregate delta within threshold passes
- **WHEN** source sum is 1,000,000 and target sum is 999,800 with a 0.1% threshold
- **THEN** the check status is PASS

#### Scenario: Aggregate delta exceeds threshold fails
- **WHEN** source sum is 1,000,000 and target sum is 990,000 with a 0.1% threshold
- **THEN** the check status is FAIL and the Result Record contains source aggregate, target aggregate, delta, and threshold

#### Scenario: Reconciliation check produces no sample rows on failure
- **WHEN** a Reconciliation check fails
- **THEN** no sample rows are written; the Result Record contains aggregate values only

### Requirement: Configurable Sample Row Count
The number of sample rows written on failure SHALL be configurable per check via the `sample_rows` field in the check's config block. When not specified, the default SHALL be 5.

#### Scenario: Custom sample row count is respected
- **WHEN** a check block specifies `sample_rows: 10` and the check fails
- **THEN** up to 10 sample rows are written for that check

#### Scenario: Default sample row count applies when not configured
- **WHEN** a failing check does not specify `sample_rows`
- **THEN** up to 5 sample rows are written

# Spec Delta

## Purpose

Defines the Config File format that engineers use to declare all validation checks for a DataGuard run — connection details, check type, parameters, and output target — without writing application code.

## ADDED Requirements

### Requirement: Config File Format
The system SHALL accept a Config File in either YAML or JSON format, treating both interchangeably. A malformed Config File SHALL be rejected at parse time with an error message identifying the offending location.

#### Scenario: Valid YAML and JSON configs produce identical behavior
- **WHEN** a YAML Config File and a semantically equivalent JSON Config File are each passed to `dataGuard run`
- **THEN** both produce identical check execution behavior and Results Store output

#### Scenario: Malformed config is rejected before execution
- **WHEN** a Config File contains a syntax error (e.g. unclosed bracket, invalid YAML indentation)
- **THEN** DataGuard exits with a non-zero code and prints a parse error identifying the file location, without executing any checks

### Requirement: Per-Check Configuration
Each check block in the Config File SHALL specify: a unique check name, a check type, a source connection, a target connection where applicable, and check-type-specific parameters. A missing required field SHALL cause DataGuard to reject the Config File at parse time, identifying the offending check by name.

#### Scenario: Check block with missing required field is rejected
- **WHEN** a check block omits a required field (e.g. `check_type` or `source`)
- **THEN** DataGuard exits with a non-zero code and names the offending check in the error message, without executing any checks

#### Scenario: Multiple check types coexist in one Config File
- **WHEN** a Config File contains checks of different types (e.g. row_count and null_threshold)
- **THEN** DataGuard executes each check independently using its own type-specific logic

### Requirement: Shared Connection References
The Config File SHALL allow engineers to define a named connection block once and reference it by name in multiple check blocks, avoiding duplication.

#### Scenario: Shared connection reference produces identical behavior to inline
- **WHEN** a Config File defines a named connection and references it in two checks
- **THEN** those checks connect identically to a config where the same connection is inlined in each check

### Requirement: Credential Handling
Connection credentials SHALL be supplied either inline in the Config File or via environment variable references. DataGuard SHALL NOT require any secrets management system beyond environment variable injection in v1.

#### Scenario: Environment variable reference resolves at runtime
- **WHEN** a connection parameter references an environment variable (e.g. `password: ${DB_PASSWORD}`)
- **THEN** DataGuard substitutes the variable's runtime value when establishing the connection

#### Scenario: Missing environment variable is reported as an error
- **WHEN** a referenced environment variable is not set at runtime
- **THEN** the affected check is recorded as ERROR with a message identifying the missing variable

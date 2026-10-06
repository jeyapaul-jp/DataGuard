# Spec Delta

## Purpose

Defines the six connector types DataGuard uses to read from source and target data stores, and the error behavior when a connection cannot be established.

## ADDED Requirements

### Requirement: SQL Connector
The system SHALL connect to any SQL-compliant database using JDBC/ODBC with host, port, database, username, and password specified in the config. Common databases include SQL Server, PostgreSQL, and Oracle.

#### Scenario: SQL connector executes a query and returns results
- **WHEN** a check specifies a SQL source with valid connection parameters
- **THEN** DataGuard connects and executes the required query, returning results for check evaluation

#### Scenario: SQL connection failure produces an ERROR result
- **WHEN** the specified SQL host is unreachable or credentials are invalid
- **THEN** the check is recorded as ERROR with the SQL error message; execution continues with remaining checks

### Requirement: File Connectors
The system SHALL read CSV, Parquet, and JSON files from local filesystem paths or cloud object storage URIs (S3, Azure Blob, GCS) as source or target for any check type.

#### Scenario: Local file is read as a data source
- **WHEN** a check specifies a local Parquet file path as its source
- **THEN** DataGuard reads the file and uses its contents for check evaluation

#### Scenario: Cloud storage URI is read as a data source
- **WHEN** a check specifies an S3 URI (e.g. `s3://bucket/path/file.csv`) as its source
- **THEN** DataGuard reads the file from cloud storage and uses its contents for check evaluation

#### Scenario: Missing or unreadable file path produces an ERROR result
- **WHEN** the specified file path does not exist or cannot be read
- **THEN** the check is recorded as ERROR with the file access error message; execution continues with remaining checks

### Requirement: Snowflake Connector
The system SHALL connect to Snowflake using account identifier, warehouse, database, schema, and credentials (username/password or key-pair) specified in the config.

#### Scenario: Snowflake connector executes a query and returns results
- **WHEN** a check specifies a Snowflake source with valid connection parameters
- **THEN** DataGuard connects and executes the required query, returning results for check evaluation

#### Scenario: Snowflake connection failure produces an ERROR result
- **WHEN** Snowflake credentials are invalid or the account is unreachable
- **THEN** the check is recorded as ERROR with the Snowflake error message; execution continues with remaining checks

### Requirement: Databricks Connector
The system SHALL connect to a Databricks SQL Warehouse using host, HTTP path, and access token specified in the config.

#### Scenario: Databricks connector executes a query and returns results
- **WHEN** a check specifies a Databricks source with valid connection parameters
- **THEN** DataGuard connects to the SQL Warehouse and executes the required query, returning results for check evaluation

#### Scenario: Databricks connection failure produces an ERROR result
- **WHEN** the Databricks access token is invalid or the warehouse is unreachable
- **THEN** the check is recorded as ERROR with the Databricks error message; execution continues with remaining checks

### Requirement: Cloud and On-Prem Portability
DataGuard SHALL run without requiring any cloud-provider SDK at runtime for on-prem deployments. Cloud connector functionality SHALL be conditionally available based on installed optional dependencies.

#### Scenario: DataGuard runs on-prem without cloud SDKs
- **WHEN** DataGuard is installed and run in an environment with no cloud provider credentials or SDKs
- **THEN** checks that use local file paths and SQL connectors execute successfully; cloud-storage checks fail with a clear missing-dependency error rather than a cryptic import error

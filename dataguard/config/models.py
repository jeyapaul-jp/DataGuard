from __future__ import annotations

from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Known result record fields and required subset
# ---------------------------------------------------------------------------

RESULT_RECORD_FIELDS: frozenset[str] = frozenset({
    "run_id", "check_name", "check_type", "status",
    "actual_value", "expected_value", "delta", "null_count",
    "source_connector_type", "target_connector_type", "timestamp", "reason",
})
REQUIRED_OUTPUT_FIELDS: frozenset[str] = frozenset({"run_id", "check_name", "status"})


# ---------------------------------------------------------------------------
# Connection models
# ---------------------------------------------------------------------------

class SqlConnection(BaseModel):
    type: Literal["sql"] = "sql"
    url: str  # SQLAlchemy DBAPI URL e.g. sqlite:///db.sqlite


class SnowflakeConnection(BaseModel):
    type: Literal["snowflake"] = "snowflake"
    account: str
    warehouse: str
    database: str
    schema_name: str
    user: str
    password: Optional[str] = None
    private_key_path: Optional[str] = None  # path to PEM file for key-pair auth


class DatabricksConnection(BaseModel):
    type: Literal["databricks"] = "databricks"
    host: str
    http_path: str
    access_token: str


class CsvConnection(BaseModel):
    type: Literal["csv"] = "csv"
    path: str


class ParquetConnection(BaseModel):
    type: Literal["parquet"] = "parquet"
    path: str


class JsonConnection(BaseModel):
    type: Literal["json"] = "json"
    path: str


Connection = Annotated[
    Union[
        SqlConnection,
        SnowflakeConnection,
        DatabricksConnection,
        CsvConnection,
        ParquetConnection,
        JsonConnection,
    ],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Check endpoint (connection reference + optional query)
# ---------------------------------------------------------------------------

class CheckEndpoint(BaseModel):
    connection: str
    query: Optional[str] = None  # required for SQL/Snowflake/Databricks; ignored for file


# ---------------------------------------------------------------------------
# Check config models — one per check type
# ---------------------------------------------------------------------------

class RowCountCheckConfig(BaseModel):
    name: str
    check_type: Literal["row_count"] = "row_count"
    source: CheckEndpoint
    target: CheckEndpoint
    threshold_pct: float = 0.0
    enabled: bool = True
    sample_rows: int = 5


class DuplicateCheckConfig(BaseModel):
    name: str
    check_type: Literal["duplicate"] = "duplicate"
    source: CheckEndpoint
    key_columns: list[str]
    enabled: bool = True
    sample_rows: int = 5


class NullThresholdCheckConfig(BaseModel):
    name: str
    check_type: Literal["null_threshold"] = "null_threshold"
    source: CheckEndpoint
    column: str
    threshold_pct: float
    enabled: bool = True
    sample_rows: int = 5


class ReferentialIntegrityCheckConfig(BaseModel):
    name: str
    check_type: Literal["referential_integrity"] = "referential_integrity"
    source: CheckEndpoint
    source_column: str
    target: CheckEndpoint
    target_column: str
    enabled: bool = True
    sample_rows: int = 5


class ReconciliationCheckConfig(BaseModel):
    name: str
    check_type: Literal["reconciliation"] = "reconciliation"
    source: CheckEndpoint
    source_column: str
    target: CheckEndpoint
    target_column: str
    aggregate: Literal["sum", "count", "avg"] = "sum"
    threshold_pct: float = 0.0
    enabled: bool = True
    sample_rows: int = 5


CheckConfig = Annotated[
    Union[
        RowCountCheckConfig,
        DuplicateCheckConfig,
        NullThresholdCheckConfig,
        ReferentialIntegrityCheckConfig,
        ReconciliationCheckConfig,
    ],
    Field(discriminator="check_type"),
]


# ---------------------------------------------------------------------------
# Output config models
# ---------------------------------------------------------------------------

def _validate_output_fields(v: Optional[list[str]]) -> Optional[list[str]]:
    if v is None:
        return v
    missing_required = REQUIRED_OUTPUT_FIELDS - set(v)
    if missing_required:
        raise ValueError(
            f"output_fields must include required fields: {sorted(missing_required)}"
        )
    invalid = set(v) - RESULT_RECORD_FIELDS
    if invalid:
        raise ValueError(
            f"Invalid output_fields {sorted(invalid)}. "
            f"Valid fields: {sorted(RESULT_RECORD_FIELDS)}"
        )
    return v


class FileOutputConfig(BaseModel):
    type: Literal["csv", "json"]
    path: str
    overwrite: bool = False
    output_fields: Optional[list[str]] = None

    @field_validator("output_fields")
    @classmethod
    def validate_output_fields(cls, v):
        return _validate_output_fields(v)


class DatabaseOutputConfig(BaseModel):
    type: Literal["database"] = "database"
    connection: str
    table: str
    output_fields: Optional[list[str]] = None

    @field_validator("output_fields")
    @classmethod
    def validate_output_fields(cls, v):
        return _validate_output_fields(v)


OutputConfig = Annotated[
    Union[FileOutputConfig, DatabaseOutputConfig],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Top-level config
# ---------------------------------------------------------------------------

class DataguardConfig(BaseModel):
    connections: dict[str, Connection] = Field(default_factory=dict)
    checks: list[CheckConfig] = Field(default_factory=list)
    output: OutputConfig

    @model_validator(mode="after")
    def check_unique_names(self) -> "DataguardConfig":
        seen: set[str] = set()
        for check in self.checks:
            if check.name in seen:
                raise ValueError(f"Duplicate check name: '{check.name}'")
            seen.add(check.name)
        return self

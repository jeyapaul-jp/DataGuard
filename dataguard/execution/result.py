from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Optional
import uuid


@dataclass
class CheckResult:
    run_id: str
    check_name: str
    check_type: str
    status: str  # PASS | FAIL | SKIP | ERROR
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None
    delta: Optional[float] = None
    null_count: Optional[int] = None
    source_connector_type: Optional[str] = None
    target_connector_type: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def new_run_id() -> str:
        return str(uuid.uuid4())

from dataclasses import dataclass
from typing import Literal, Any, Protocol


@dataclass
class BaseResult(Protocol):
    status: Literal["OK", "Failed"] = "OK"
    errors: set[str] | list[str] | None = None
    result: Any | None = None

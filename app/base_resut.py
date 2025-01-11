from dataclasses import dataclass
from typing import Literal, Any, Protocol, runtime_checkable


@dataclass
class BaseResult(Protocol):
    errors: set[str] | list[str] | bool| None = None
    result: Any | None = None

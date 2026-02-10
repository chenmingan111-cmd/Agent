from typing import Literal, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DraftRequest(BaseModel):
    index: str
    nl_query: str
    mode: Literal["preview", "execute"] = "preview"
    user_context: Dict[str, Any] = Field(default_factory=dict)

class DraftResponse(BaseModel):
    dsl: Dict[str, Any]
    explanation: List[str]
    risk: Dict[str, Any]
    confidence: float

class ValidateRequest(BaseModel):
    index: str
    dsl: Dict[str, Any]

class ValidateResponse(BaseModel):
    valid: bool
    errors: List[str] = []
    auto_fixed: bool = False
    fixed_dsl: Optional[Dict[str, Any]] = None
    warnings: List[str] = []

class RunRequest(BaseModel):
    index: str
    dsl: Dict[str, Any]
    timeout_ms: int = 2000

class RunResponse(BaseModel):
    took: int
    timed_out: bool
    hits: Dict[str, Any]
    aggs: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = []

class ExplainRequest(BaseModel):
    index: str
    doc_id: str
    dsl: Dict[str, Any]

class ExplainResponse(BaseModel):
    matched: bool
    explanation: Dict[str, Any]

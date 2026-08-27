from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RetrieveRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: str
    top_k: int = Field(default=5, ge=1, le=20)
    retriever: str = Field(default="hybrid")
    use_reranker: bool = False
    debug: bool = Field(default=False, alias="return_debug")


class RetrieveResult(BaseModel):
    chunk_id: str
    doc_id: str
    score: float
    rank: int
    text: str
    source_url: str
    heading_path: list[str]
    authority_level: str
    domain: str
    component_scores: dict[str, float]


class RetrieveResponse(BaseModel):
    results: list[RetrieveResult]
    retriever: str
    backend: str
    debug: dict | None = None


class AskRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: str
    top_k: int = Field(default=5, ge=1, le=20)
    debug: bool = Field(default=False, alias="return_debug")
    use_reranker: bool = False
    use_guardrail: bool = True


class Citation(BaseModel):
    doc_id: str
    chunk_id: str
    source_url: str
    heading_path: list[str]
    quoted_evidence: str


class CitationVerification(BaseModel):
    is_valid: bool
    errors: list[str] = []


class EvidenceState(BaseModel):
    state: str
    reasons: list[str] = []


class GenerationTrace(BaseModel):
    provider: str | None = None
    model: str | None = None
    fallback_used: bool | None = None
    error: str | None = None
    latency_ms: float | None = None


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float
    refusal: bool
    refusal_reason: str | None = None
    citation_verification: CitationVerification | None = None
    evidence_state: EvidenceState | None = None
    generation: GenerationTrace | None = None
    retrieval_debug: dict = {}


class AgentToolCall(BaseModel):
    name: str
    arguments: dict = {}


class AgentAskRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: str
    top_k: int = Field(default=5, ge=1, le=5)
    debug: bool = Field(default=False, alias="return_debug")


class AgentAskResponse(BaseModel):
    answer: str
    confidence: float
    citations: list[Citation]
    retrieved_chunks: list[RetrieveResult]
    provider: str
    model: str
    provider_status: dict
    generation_mode: str
    tool_calls: list[AgentToolCall]
    latency_ms: float
    fallback_used: bool
    fallback_reason: str | None = None
    citations_verified: bool = False
    citation_verification: CitationVerification | None = None
    evidence_state: EvidenceState | None = None
    refusal: bool
    refusal_reason: str | None = None
    debug: dict = {}

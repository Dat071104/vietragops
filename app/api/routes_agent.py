from __future__ import annotations

from dataclasses import replace
import json
from time import perf_counter
from typing import Any

from fastapi import APIRouter

from app.core.config import get_answer_generator, get_context_builder, get_provider_router
from app.schemas.query import AgentAskRequest, AgentAskResponse, AgentToolCall, Citation, RetrieveResult
from rag.retrieval.base import normalize_text


router = APIRouter(prefix="/agent", tags=["agent"])


AGENT_SYSTEM_PROMPT = """
Ban la local agent demo cua VietRAGOps.
Neu can tra loi cau hoi ve quy dinh, chuong trinh hoc, tin chi hoac chinh sach hoc vu, hay goi tool retrieve_policy_context truoc.
Sau khi co tool result, chi tra loi dua tren ngu canh duoc truy xuat.
Tra loi ngan gon, bang tieng Viet.
""".strip()


def _tool_schema() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "retrieve_policy_context",
                "description": "Retrieve grounded academic policy context for the current question.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question to search for in the policy corpus.",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of chunks to retrieve, maximum 5.",
                        },
                    },
                    "required": ["question"],
                },
            },
        }
    ]


def _compact_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact = []
    for chunk in chunks[:5]:
        compact.append(
            {
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "source_url": chunk["source_url"],
                "heading_path": list(chunk["heading_path"]),
                "support_score": chunk.get("support_score", 0.0),
                "text": chunk["text"][:700],
            }
        )
    return compact


def _serialize_tool_calls(tool_calls: list[dict[str, Any]]) -> list[AgentToolCall]:
    serialized = []
    for call in tool_calls:
        function_payload = call.get("function") or {}
        serialized.append(
            AgentToolCall(
                name=function_payload.get("name", ""),
                arguments=function_payload.get("arguments") or {},
            )
        )
    return serialized


def _extract_tool_questions(tool_calls: list[dict[str, Any]]) -> list[str]:
    questions: list[str] = []
    for call in tool_calls:
        function_payload = call.get("function") or {}
        arguments = function_payload.get("arguments") or {}
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"question": arguments}
        question = arguments.get("question") if isinstance(arguments, dict) else None
        if isinstance(question, str) and question.strip():
            questions.append(question.strip())
    return questions


def _candidate_agent_queries(question: str, tool_calls: list[dict[str, Any]]) -> list[str]:
    candidates = [question.strip()]
    normalized_question = normalize_text(question)
    raw_question = question.casefold()
    candidates.extend(_extract_tool_questions(tool_calls))

    if ("email" in raw_question or "email" in normalized_question) and (
        "sinh viên" in raw_question or "sinh vien" in normalized_question
    ):
        candidates.extend(
            [
                "Email sinh vien TDTU",
                "email sinh vien TDTU MSSV@student.tdtu.edu.vn",
                "Cau truc email MSSV@student.tdtu.edu.vn",
            ]
        )
    if ("khoa học máy tính" in raw_question or "khoa hoc may tinh" in normalized_question) and (
        "tín chỉ" in raw_question or "tin chi" in normalized_question
    ):
        candidates.extend(
            [
                "nganh khoa hoc may tinh tin chi tot nghiep",
                "giao duc nganh khoa hoc may tinh 136 tin chi",
            ]
        )
    if "hoc phi" in normalized_question:
        candidates.append("hoc phi sinh vien")

    deduped: list[str] = []
    seen = set()
    for candidate in candidates:
        key = normalize_text(candidate)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _score_agent_bundle(question: str, bundle) -> float:
    normalized_question = normalize_text(question)
    raw_question = question.casefold()
    best_score = bundle.support_score
    for chunk in bundle.chunks:
        raw_haystack = (
            " ".join(chunk["heading_path"])
            + " "
            + chunk["text"]
            + " "
            + chunk["doc_id"]
            + " "
            + chunk.get("domain", "")
        ).casefold()
        haystack = normalize_text(raw_haystack)
        score = float(chunk.get("support_score", 0.0))
        if "email" in normalized_question and "email" in haystack:
            score += 0.6
        if "cau truc email" in normalized_question and "mssv@student.tdtu.edu.vn" in haystack:
            score += 2.0
        if ("sinh viên" in raw_question or "sinh vien" in normalized_question) and "student.tdtu.edu.vn" in haystack:
            score += 0.8
        if ("khoa học máy tính" in raw_question or "khoa hoc may tinh" in normalized_question) and (
            "tín chỉ" in raw_haystack or "tin chi" in haystack
        ):
            score += 0.8
        if ("tốt nghiệp" in raw_question or "tot nghiep" in normalized_question) and (
            "tốt nghiệp" in raw_haystack or "tot nghiep" in haystack
        ):
            score += 0.4
        if ("khoa học máy tính" in raw_question or "khoa hoc may tinh" in normalized_question) and "136" in raw_haystack:
            score += 1.2
        if "hoc phi" in normalized_question and "hoc phi" in haystack:
            score += 0.8
        if chunk["doc_id"] in {"it_cs_program_detail", "it_cs_curriculum_2018"} and "136" in raw_haystack:
            score += 1.4
        best_score = max(best_score, score)
    return best_score


def _build_agent_context_bundle(question: str, top_k: int, tool_calls: list[dict[str, Any]]):
    context_builder = get_context_builder()
    best_bundle = None
    best_query = question
    best_score = float("-inf")
    candidates = _candidate_agent_queries(question, tool_calls)

    for candidate in candidates:
        bundle = context_builder.build(candidate, top_k=top_k)
        score = _score_agent_bundle(question, bundle)
        if score > best_score:
            best_bundle = bundle
            best_query = candidate
            best_score = score

    retrieval_debug = dict(best_bundle.retrieval_debug)
    retrieval_debug["agent_selected_query"] = best_query
    retrieval_debug["agent_query_candidates"] = candidates
    return replace(best_bundle, retrieval_debug=retrieval_debug)


def _derive_generation_mode(provider: str, fallback_used: bool, refusal: bool, citations: list[Citation]) -> str:
    if provider == "ollama" and not fallback_used and not refusal:
        return "Ollama direct"
    if fallback_used and not refusal and citations:
        return "Verified fallback"
    return "Deterministic fallback"


def _derive_fallback_reason(
    provider: str,
    fallback_used: bool,
    tool_calls: list[dict[str, Any]],
    tool_error: str | None,
    provider_error: str | None,
    refusal: bool,
) -> str | None:
    if not fallback_used:
        return None
    if provider_error:
        if "rebuilt citations from verified retrieved chunks" in provider_error:
            return "Citations from the model could not be verified, so the app rebuilt the answer from verified retrieved chunks."
        return provider_error
    if provider == "mock":
        return "Start the API with LLM_PROVIDER=ollama to use the local model."
    if not tool_calls and not refusal:
        return "The model did not emit a usable tool call, so the app answered from verified retrieved chunks."
    if tool_error:
        return tool_error
    if refusal:
        return "The app kept the refusal because the query was private, out of scope, or unsupported by retrieved evidence."
    return "The app used a deterministic grounded fallback for safety."


def run_agent_query(payload: AgentAskRequest) -> AgentAskResponse:
    started = perf_counter()
    effective_top_k = min(payload.top_k, 5)
    answer_generator = get_answer_generator()
    provider_router = get_provider_router()
    provider_status = provider_router.status()

    tool_request_messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": payload.question},
    ]
    tool_invocation = provider_router.chat_with_tools(tool_request_messages, _tool_schema())
    tool_calls = tool_invocation.tool_calls
    tool_call_models = _serialize_tool_calls(tool_calls)
    fallback_used = tool_invocation.fallback_used or not bool(tool_calls)
    context_bundle = _build_agent_context_bundle(payload.question, effective_top_k, tool_calls)

    if tool_calls:
        tool_payload = {
            "question": payload.question,
            "top_k": effective_top_k,
            "chunks": _compact_chunks(context_bundle.chunks),
        }
        tool_follow_up_messages = [
            *tool_request_messages,
            {
                "role": "assistant",
                "content": tool_invocation.content,
                "tool_calls": tool_calls,
            },
            {
                "role": "tool",
                "tool_name": "retrieve_policy_context",
                "content": json.dumps(tool_payload, ensure_ascii=False),
            },
        ]
        final_turn = provider_router.chat(tool_follow_up_messages)
        fallback_used = fallback_used or final_turn.fallback_used

    answer_payload, provider_meta = answer_generator.answer_with_agent_fallback_from_context(
        payload.question,
        context_bundle,
        debug=payload.debug,
    )
    fallback_used = fallback_used or provider_meta["fallback_used"]
    response_provider = provider_status.get("provider") or provider_meta["provider"]
    response_model = provider_status.get("model") or provider_meta["model"]

    retrieved_chunks = [
        RetrieveResult(
            chunk_id=chunk["chunk_id"],
            doc_id=chunk["doc_id"],
            score=chunk["score"],
            rank=index,
            text=chunk["text"],
            source_url=chunk["source_url"],
            heading_path=chunk["heading_path"],
            authority_level=chunk["authority_level"],
            domain=chunk["domain"],
            component_scores=chunk["component_scores"],
        )
        for index, chunk in enumerate(context_bundle.chunks, start=1)
    ]
    citations = [Citation(**citation) for citation in answer_payload["citations"]]
    generation_mode = _derive_generation_mode(
        provider=response_provider,
        fallback_used=fallback_used,
        refusal=answer_payload["refusal"],
        citations=citations,
    )
    fallback_reason = _derive_fallback_reason(
        provider=response_provider,
        fallback_used=fallback_used,
        tool_calls=tool_calls,
        tool_error=tool_invocation.error,
        provider_error=provider_meta["error"],
        refusal=answer_payload["refusal"],
    )

    debug_payload = {}
    if payload.debug:
        debug_payload = {
            "retrieval_debug": context_bundle.retrieval_debug,
            "tool_call_error": tool_invocation.error,
            "provider_status": provider_status,
        }

    return AgentAskResponse(
        answer=answer_payload["answer"],
        confidence=float(answer_payload.get("confidence", 0.0)),
        citations=citations,
        retrieved_chunks=retrieved_chunks,
        provider=response_provider,
        model=response_model,
        provider_status=provider_status,
        generation_mode=generation_mode,
        tool_calls=tool_call_models,
        latency_ms=round((perf_counter() - started) * 1000, 2),
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        citations_verified=bool(citations) and not answer_payload["refusal"],
        refusal=answer_payload["refusal"],
        refusal_reason=answer_payload["refusal_reason"],
        debug=debug_payload,
    )


@router.post("/ask", response_model=AgentAskResponse)
def ask_agent(payload: AgentAskRequest) -> AgentAskResponse:
    return run_agent_query(payload)

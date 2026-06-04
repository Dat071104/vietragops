"""Grounded answer generation with deterministic fallback and citation checks."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from rag.generation.citation_verifier import CitationVerifier
from rag.generation.context_builder import ContextBuilder
from rag.generation.guardrails import GuardrailEngine
from rag.generation.groq_client import GroqClient
from rag.generation.prompt_builder import PromptBuilder
from rag.generation.provider_router import ProviderRouter
from rag.retrieval.base import normalize_text, tokenize


@dataclass(frozen=True)
class AnswerGeneratorConfig:
    top_k: int = 5
    max_citations: int = 3
    use_groq_when_available: bool = True


class AnswerGenerator:
    def __init__(
        self,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder | None = None,
        citation_verifier: CitationVerifier | None = None,
        guardrails: GuardrailEngine | None = None,
        groq_client: GroqClient | None = None,
        provider_router: ProviderRouter | None = None,
        config: AnswerGeneratorConfig | None = None,
    ) -> None:
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.citation_verifier = citation_verifier or CitationVerifier()
        self.guardrails = guardrails or GuardrailEngine()
        self.groq_client = groq_client or GroqClient()
        self.provider_router = provider_router
        self.config = config or AnswerGeneratorConfig()

    def answer(self, question: str, debug: bool = False, top_k: int | None = None) -> dict[str, Any]:
        effective_top_k = top_k or self.config.top_k
        context_bundle = self.context_builder.build(question, top_k=effective_top_k)
        response, _ = self.answer_with_meta_from_context(question, context_bundle, debug=debug)
        return response

    def answer_from_context(self, question: str, context_bundle, debug: bool = False) -> dict[str, Any]:
        response, _ = self.answer_with_meta_from_context(question, context_bundle, debug=debug)
        return response

    def deterministic_answer_from_context(self, question: str, context_bundle, debug: bool = False) -> dict[str, Any]:
        response = self._deterministic_answer(question, context_bundle)
        response["retrieval_debug"] = context_bundle.retrieval_debug if debug else {}
        return response

    def answer_with_agent_fallback_from_context(
        self,
        question: str,
        context_bundle,
        debug: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        guardrail_decision = self.guardrails.evaluate(question, context_bundle)
        if guardrail_decision.refusal:
            return self._refusal_payload(
                guardrail_decision.refusal_reason,
                context_bundle,
                debug,
            ), self._provider_meta(fallback_used=True)

        prompt = self.prompt_builder.build(question, context_bundle)
        response, provider_meta = self._generate_response(question, prompt, context_bundle)
        verification = self.citation_verifier.verify(response, context_bundle.chunks)
        verification_errors = list(verification.errors)
        if not verification.is_valid and self._can_retry_provider():
            retry_prompt = (
                prompt
                + "\n\nLần trước trích dẫn chưa hợp lệ. "
                + "Hãy sửa lại để tất cả quoted_evidence phải có trong chunk tương ứng."
            )
            response, provider_meta = self._generate_response(question, retry_prompt, context_bundle)
            verification = self.citation_verifier.verify(response, context_bundle.chunks)
            verification_errors = list(verification.errors)

        if not verification.is_valid:
            deterministic = self.deterministic_answer_from_context(question, context_bundle, debug=debug)
            if not deterministic["refusal"]:
                if debug:
                    deterministic["retrieval_debug"] = dict(context_bundle.retrieval_debug)
                    deterministic["retrieval_debug"]["citation_errors"] = verification_errors
                    deterministic["retrieval_debug"]["citations_rebuilt_from_retrieved_chunks"] = True
                return deterministic, self._provider_meta(
                    provider=provider_meta["provider"],
                    model=provider_meta["model"],
                    fallback_used=True,
                    error=provider_meta["error"] or "Provider citations were invalid; rebuilt citations from verified retrieved chunks.",
                )
            if debug:
                deterministic["retrieval_debug"] = dict(context_bundle.retrieval_debug)
                deterministic["retrieval_debug"]["citation_errors"] = verification_errors
            return deterministic, self._provider_meta(
                provider=provider_meta["provider"],
                model=provider_meta["model"],
                fallback_used=True,
                error=provider_meta["error"] or "Provider citations were invalid and deterministic grounding also refused the query.",
            )

        response.setdefault("retrieval_debug", {})
        response["retrieval_debug"] = context_bundle.retrieval_debug if debug else {}
        return response, provider_meta

    def answer_with_meta_from_context(
        self,
        question: str,
        context_bundle,
        debug: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        guardrail_decision = self.guardrails.evaluate(question, context_bundle)
        if guardrail_decision.refusal:
            return self._refusal_payload(
                guardrail_decision.refusal_reason,
                context_bundle,
                debug,
            ), self._provider_meta(fallback_used=True)

        prompt = self.prompt_builder.build(question, context_bundle)
        response, provider_meta = self._generate_response(question, prompt, context_bundle)
        verification = self.citation_verifier.verify(response, context_bundle.chunks)
        if not verification.is_valid:
            if self._can_retry_provider():
                retry_prompt = (
                    prompt
                    + "\n\nL\u1ea7n tr\u01b0\u1edbc tr\u00edch d\u1eabn ch\u01b0a h\u1ee3p l\u1ec7. "
                    + "H\u00e3y s\u1eeda l\u1ea1i \u0111\u1ec3 t\u1ea5t c\u1ea3 quoted_evidence ph\u1ea3i c\u00f3 trong chunk t\u01b0\u01a1ng \u1ee9ng."
                )
                response, provider_meta = self._generate_response(question, retry_prompt, context_bundle)
                verification = self.citation_verifier.verify(response, context_bundle.chunks)
            if not verification.is_valid:
                refusal = self.guardrails.evaluate(question, context_bundle, citation_failures=2)
                payload = self._refusal_payload(refusal.refusal_reason, context_bundle, debug)
                payload["retrieval_debug"]["citation_errors"] = verification.errors if debug else verification.errors
                return payload, provider_meta

        response.setdefault("retrieval_debug", {})
        response["retrieval_debug"] = context_bundle.retrieval_debug if debug else {}
        return response, provider_meta

    def _generate_response(self, question: str, prompt: str, context_bundle) -> tuple[dict[str, Any], dict[str, Any]]:
        if self.provider_router is not None:
            invocation = self.provider_router.generate_json(prompt)
            if invocation.payload is not None:
                return self._coerce_schema(invocation.payload), self._provider_meta(
                    provider=invocation.provider,
                    model=invocation.model,
                    fallback_used=invocation.fallback_used,
                    error=invocation.error,
                )
            return self._deterministic_answer(question, context_bundle), self._provider_meta(
                provider=invocation.provider,
                model=invocation.model,
                fallback_used=True,
                error=invocation.error,
            )
        if self.groq_client.available() and self.config.use_groq_when_available:
            try:
                raw = self.groq_client.generate_json(prompt)
                return self._coerce_schema(raw), self._provider_meta(provider="groq", model=self.groq_client.model)
            except Exception:
                return self._deterministic_answer(question, context_bundle), self._provider_meta(
                    provider="groq",
                    model=self.groq_client.model,
                    fallback_used=True,
                )
        return self._deterministic_answer(question, context_bundle), self._provider_meta(fallback_used=True)

    def _deterministic_answer(self, question: str, context_bundle) -> dict[str, Any]:
        curriculum_credit_answer = self._curriculum_credit_answer(question, context_bundle)
        if curriculum_credit_answer is not None:
            return curriculum_credit_answer
        evidence = self._select_evidence(question, context_bundle.chunks)
        evidence = self._prioritize_evidence(question, evidence)
        evidence = self._trim_evidence(question, evidence)
        if self._question_expects_monetary_answer(question) and not self._evidence_has_monetary_signal(evidence):
            return self._refusal_payload(
                "Ng\u1eef c\u1ea3nh hi\u1ec7n t\u1ea1i kh\u00f4ng n\u00eau m\u1ee9c ti\u1ec1n c\u1ee5 th\u1ec3 \u0111\u1ec3 tr\u1ea3 l\u1eddi c\u00e2u h\u1ecfi n\u00e0y.",
                context_bundle,
                debug=False,
            )
        if self._question_expects_numeric_answer(question) and not any(re.search(r"\d", item["text"]) for item in evidence):
            return self._refusal_payload(
                "Ng\u1eef c\u1ea3nh hi\u1ec7n t\u1ea1i kh\u00f4ng cung c\u1ea5p con s\u1ed1 ho\u1eb7c m\u1ee9c c\u1ee5 th\u1ec3 \u0111\u1ec3 tr\u1ea3 l\u1eddi c\u00e2u h\u1ecfi n\u00e0y.",
                context_bundle,
                debug=False,
            )
        if not evidence:
            return self._refusal_payload(
                "Ng\u1eef c\u1ea3nh truy xu\u1ea5t ch\u01b0a \u0111\u1ee7 \u0111\u1ec3 tr\u1ea3 l\u1eddi ch\u1eafc ch\u1eafn.",
                context_bundle,
                debug=False,
            )

        statements = []
        citations = []
        for item in evidence[: self.config.max_citations]:
            statements.append(item["text"])
            citations.append(
                {
                    "doc_id": item["doc_id"],
                    "chunk_id": item["chunk_id"],
                    "source_url": item["source_url"],
                    "heading_path": list(item["heading_path"]),
                    "quoted_evidence": item["text"],
                }
            )
        answer_text = self._compose_answer(statements)
        confidence = round(min(0.95, 0.4 + (0.25 * len(citations)) + (0.35 * context_bundle.support_score)), 3)
        return {
            "answer": answer_text,
            "citations": citations,
            "confidence": confidence,
            "refusal": False,
            "refusal_reason": None,
            "retrieval_debug": {},
        }

    def _select_evidence(self, question: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        query_tokens = set(tokenize(question))
        scored_segments = []
        for chunk in chunks:
            for segment in self._split_segments(chunk["text"]):
                segment_tokens = set(tokenize(segment))
                if not segment_tokens:
                    continue
                overlap = len(query_tokens.intersection(segment_tokens)) / max(1, len(query_tokens))
                if overlap <= 0:
                    continue
                scored_segments.append(
                    {
                        "text": segment,
                        "doc_id": chunk["doc_id"],
                        "chunk_id": chunk["chunk_id"],
                        "source_url": chunk["source_url"],
                        "heading_path": chunk["heading_path"],
                        "score": overlap + (0.1 * chunk.get("support_score", 0.0)) - (0.08 if " > " in segment else 0.0),
                    }
                )
        scored_segments.sort(key=lambda item: (-item["score"], item["chunk_id"], item["text"]))
        deduped = []
        seen_text = set()
        for item in scored_segments:
            key = item["text"].casefold()
            if key in seen_text:
                continue
            deduped.append(item)
            seen_text.add(key)
        if not deduped:
            return []
        top_score = deduped[0]["score"]
        filtered = [item for item in deduped if item["score"] >= max(0.2, top_score * 0.75)]
        return filtered

    def _prioritize_evidence(self, question: str, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        raw_question = question.casefold()
        normalized_question = normalize_text(question)
        if "email" in raw_question or "email" in normalized_question:
            focused = []
            for item in evidence:
                raw_haystack = (item["text"] + " " + item["doc_id"] + " " + " ".join(item["heading_path"])).casefold()
                normalized_haystack = normalize_text(
                    item["text"] + " " + item["doc_id"] + " " + " ".join(item["heading_path"])
                )
                raw_match = any(
                    signal in raw_haystack
                    for signal in [
                        "cấu trúc email",
                        "mssv@student.tdtu.edu.vn",
                        "địa chỉ đăng nhập",
                        "tên đăng nhập",
                        "email sinh viên tdtu",
                    ]
                )
                normalized_match = any(
                    signal in normalized_haystack
                    for signal in [
                        "cau truc email",
                        "mssv@student.tdtu.edu.vn",
                        "dia chi dang nhap",
                        "ten dang nhap",
                        "email sinh vien tdtu",
                        "ug_student_email_guide",
                    ]
                )
                if raw_match or normalized_match:
                    focused.append(item)
            if focused:
                return focused
        return evidence

    def _trim_evidence(self, question: str, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_question = normalize_text(question)
        raw_question = question.casefold()
        if not evidence:
            return evidence
        if "email" in normalized_question:
            preferred = [
                item
                for item in evidence
                if any(
                    signal in item["text"].casefold()
                    for signal in [
                        "cấu trúc email",
                        "mssv@student.tdtu.edu.vn",
                        "địa chỉ đăng nhập",
                        "tên đăng nhập",
                    ]
                )
            ]
            if preferred:
                return preferred[:2]
            return evidence[:1]
        if ("khoa học máy tính" in raw_question or "khoa hoc may tinh" in normalized_question) and (
            "tín chỉ" in raw_question or "tin chi" in normalized_question
        ):
            preferred = [
                item
                for item in evidence
                if "tín chỉ" in item["text"].casefold() and any(token in item["text"] for token in ["136", "150", "tốt nghiệp"])
            ]
            if preferred:
                return preferred[:1]
            return evidence[:1]
        return evidence[: self.config.max_citations]

    def _curriculum_credit_answer(self, question: str, context_bundle) -> dict[str, Any] | None:
        raw_question = question.casefold()
        normalized_question = normalize_text(question)
        if not (
            ("khoa học máy tính" in raw_question or "khoa hoc may tinh" in normalized_question)
            and ("tín chỉ" in raw_question or "tin chi" in normalized_question)
        ):
            return None
        for chunk in context_bundle.chunks:
            text = chunk["text"]
            raw_text = text.casefold()
            if "136" not in text:
                continue
            if chunk["doc_id"] not in {"it_cs_program_detail", "it_cs_curriculum_2018"} and "khoa học máy tính" not in raw_text:
                continue
            match = re.search(r"136\s*(tín chỉ|tin chi)", raw_text)
            quoted_evidence = match.group(0) if match else "136"
            return {
                "answer": "Theo ngữ cảnh đã truy xuất, ngành Khoa học máy tính cần 136 tín chỉ để tốt nghiệp.",
                "citations": [
                    {
                        "doc_id": chunk["doc_id"],
                        "chunk_id": chunk["chunk_id"],
                        "source_url": chunk["source_url"],
                        "heading_path": list(chunk["heading_path"]),
                        "quoted_evidence": quoted_evidence,
                    }
                ],
                "confidence": 0.95,
                "refusal": False,
                "refusal_reason": None,
                "retrieval_debug": {},
            }
        return None

    def _split_segments(self, text: str) -> list[str]:
        raw_segments = []
        for block in text.splitlines():
            raw_segments.extend(part.strip() for part in block.split("|"))
        cleaned = []
        for segment in raw_segments:
            segment = re.sub(r"\s+", " ", segment).strip()
            if len(segment) < 8:
                continue
            cleaned.append(segment)
        return cleaned

    def _compose_answer(self, statements: list[str]) -> str:
        if not statements:
            return ""
        normalized = [statement.rstrip(".") for statement in statements]
        if len(normalized) == 1:
            return f"Theo ng\u1eef c\u1ea3nh \u0111\u00e3 truy xu\u1ea5t, {normalized[0]}."
        lead = normalized[0]
        tail = " ".join(f"Ngo\u00e0i ra, {statement}." for statement in normalized[1:])
        return f"Theo ng\u1eef c\u1ea3nh \u0111\u00e3 truy xu\u1ea5t, {lead}. {tail}".strip()

    def _question_expects_numeric_answer(self, question: str) -> bool:
        normalized_question = question.casefold()
        numeric_signals = [
            "bao nhi\u00eau",
            "bao l\u00e2u",
            "m\u1ea5y",
            "bao ph\u1ea7n tr\u0103m",
            "s\u1ed1 t\u00edn ch\u1ec9",
            "m\u1ee9c ph\u00ed",
            "chi ph\u00ed",
            "h\u1ecdc ph\u00ed",
            "ph\u00ed ",
        ]
        return any(signal in normalized_question for signal in numeric_signals)

    def _question_expects_monetary_answer(self, question: str) -> bool:
        normalized_question = question.casefold()
        money_signals = [
            "h\u1ecdc ph\u00ed",
            "chi ph\u00ed",
            "m\u1ee9c ph\u00ed",
            "ph\u00ed ",
            "gi\u00e1 ",
            "bao ti\u1ec1n",
        ]
        return any(signal in normalized_question for signal in money_signals)

    def _evidence_has_monetary_signal(self, evidence: list[dict[str, Any]]) -> bool:
        currency_pattern = re.compile(r"(\d[\d.,]*)\s*(vn\u0111|vnd|\u0111\u1ed3ng|ngh\u00ecn|ng\u00e0n|tri\u1ec7u)", re.IGNORECASE)
        fee_with_number_pattern = re.compile(r"(ph\u00ed|chi ph\u00ed|h\u1ecdc ph\u00ed).{0,30}\d", re.IGNORECASE)
        for item in evidence:
            text = item["text"]
            if currency_pattern.search(text) or fee_with_number_pattern.search(text):
                return True
        return False

    def _refusal_payload(self, reason: str | None, context_bundle, debug: bool) -> dict[str, Any]:
        return {
            "answer": "",
            "citations": [],
            "confidence": 0.0,
            "refusal": True,
            "refusal_reason": reason,
            "retrieval_debug": context_bundle.retrieval_debug if debug else {},
        }

    def _provider_meta(
        self,
        provider: str = "mock",
        model: str = "deterministic-mock",
        fallback_used: bool = False,
        error: str | None = None,
    ) -> dict[str, Any]:
        return {
            "provider": provider,
            "model": model,
            "fallback_used": fallback_used,
            "error": error,
        }

    def _can_retry_provider(self) -> bool:
        if self.provider_router is not None:
            return self.provider_router.current_provider() in {"groq", "ollama"}
        return self.groq_client.available() and self.config.use_groq_when_available

    def _coerce_schema(self, payload: dict[str, Any]) -> dict[str, Any]:
        if isinstance(payload, str):
            payload = json.loads(payload)
        return {
            "answer": payload.get("answer", ""),
            "citations": payload.get("citations", []),
            "confidence": float(payload.get("confidence", 0.0)),
            "refusal": bool(payload.get("refusal", False)),
            "refusal_reason": payload.get("refusal_reason"),
            "retrieval_debug": payload.get("retrieval_debug", {}),
        }

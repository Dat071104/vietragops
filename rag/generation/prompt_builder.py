"""Prompt construction for grounded answer generation."""

from __future__ import annotations

from rag.generation.context_builder import ContextBundle


class PromptBuilder:
    def build(self, question: str, context_bundle: ContextBundle) -> str:
        context_blocks = []
        for chunk in context_bundle.chunks:
            context_blocks.append(
                "\n".join(
                    [
                        f"[CHUNK] {chunk['chunk_id']}",
                        f"doc_id: {chunk['doc_id']}",
                        f"source_url: {chunk['source_url']}",
                        f"heading_path: {' > '.join(chunk['heading_path'])}",
                        f"text: {chunk['text']}",
                    ]
                )
            )

        return "\n\n".join(
            [
                "B\u1ea1n l\u00e0 b\u1ed9 m\u00e1y tr\u1ea3 l\u1eddi c\u00e2u h\u1ecfi cho VietRAGOps.",
                "Ch\u1ec9 \u0111\u01b0\u1ee3c tr\u1ea3 l\u1eddi d\u1ef1a tr\u00ean NG\u1eee C\u1ea2NH \u0111\u01b0\u1ee3c cung c\u1ea5p.",
                "M\u1ecdi kh\u1eb3ng \u0111\u1ecbnh th\u1ef1c t\u1ebf ph\u1ea3i c\u00f3 tr\u00edch d\u1eabn.",
                "N\u1ebfu ng\u1eef c\u1ea3nh kh\u00f4ng \u0111\u1ee7 ho\u1eb7c c\u00e2u h\u1ecfi n\u1eb1m ngo\u00e0i ph\u1ea1m vi d\u1eef li\u1ec7u, h\u00e3y t\u1eeb ch\u1ed1i.",
                "N\u1ebfu c\u00f3 xung \u0111\u1ed9t ngu\u1ed3n, \u01b0u ti\u00ean ngu\u1ed3n ch\u00ednh th\u1ee9c v\u00e0 m\u1edbi h\u01a1n.",
                "Kh\u00f4ng tr\u1ea3 l\u1eddi c\u00e2u h\u1ecfi v\u1ec1 d\u1eef li\u1ec7u c\u00e1 nh\u00e2n ho\u1eb7c ri\u00eang t\u01b0 n\u1ebfu ng\u1eef c\u1ea3nh kh\u00f4ng c\u00f4ng khai h\u1ed7 tr\u1ee3.",
                "Tr\u1ea3 l\u1eddi b\u1eb1ng ti\u1ebfng Vi\u1ec7t.",
                "Tr\u1ea3 v\u1ec1 JSON \u0111\u00fang schema sau:",
                '{ "answer": "...", "citations": [{"doc_id": "...", "chunk_id": "...", "source_url": "...", "heading_path": ["..."], "quoted_evidence": "..."}], "confidence": 0.0, "refusal": false, "refusal_reason": null, "retrieval_debug": {} }',
                f"C\u00c2U H\u1eceI: {question}",
                "NG\u1eee C\u1ea2NH:",
                "\n\n".join(context_blocks) if context_blocks else "(kh\u00f4ng c\u00f3 ng\u1eef c\u1ea3nh)",
            ]
        )

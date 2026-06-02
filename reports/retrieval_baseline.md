# Retrieval Baseline

## Setup

- Chunks: `data/chunks/chunks_500.jsonl`
- QA set: `evals/datasets/dev_qa.jsonl`
- Questions: 20 total, 18 answerable, 2 unanswerable
- `top_k`: 5

## Metrics

| Retriever | Backend | Recall@3 | Recall@5 | Recall@10 | MRR | Precision@5 | Avg latency (ms) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BM25 | `offline_bm25` | 0.7222 | 0.8889 | 0.8889 | 0.5917 | 0.1889 | 2.62 |
| Dense | `sparse_semantic_fallback` | 0.6667 | 0.7778 | 0.7778 | 0.4694 | 0.1667 | 14.47 |
| Hybrid | `rrf(offline_bm25+sparse_semantic_fallback)` | 0.8333 | 0.8889 | 0.8889 | 0.5972 | 0.1889 | 18.52 |

## Key findings

- Hybrid delivered the best `Recall@3` and the best `MRR` on the dev set.
- BM25 remained the fastest baseline by a wide margin and matched hybrid on `Recall@5`.
- The dense fallback was reproducible and fully offline, but weaker on list-heavy registration and schedule questions.

## Cases improved by hybrid

- `dev_q003`: hybrid moved the email structure chunk to rank 1.
- `dev_q004`: hybrid improved ranking for the school-issued email guidance chunk.
- `dev_q018`: hybrid improved retrieval for the stricter graduation-conditions question from the 2021 regulation.

## Common misses

- `dev_q005`: the yearly semester-structure question was dominated by generic regulation chunks that repeat `học kỳ` heavily.
- `dev_q009`: the overload-registration question was often pulled toward regulation chunks about credit limits instead of the specific support-office instruction in the student guide.

## Recommendation for Phase 5

- Keep `chunks_500.jsonl` as the default benchmark corpus.
- Use hybrid retrieval as the starting point for reranking and source-priority experiments.
- Target improvements on schedule and overloaded-registration questions, where baseline lexical overlap is noisy.

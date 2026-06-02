#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from statistics import mean


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    p = argparse.ArgumentParser(description='Compute basic retrieval metrics from JSONL predictions.')
    p.add_argument('--predictions', required=True, help='jsonl with question_id and retrieved_chunk_ids')
    p.add_argument('--qa', required=True, help='jsonl with question_id and relevant_chunk_ids')
    p.add_argument('--k', default='3,5,10')
    args = p.parse_args()

    ks = [int(x) for x in args.k.split(',')]
    qa = {row['question_id']: set(row.get('relevant_chunk_ids', [])) for row in read_jsonl(args.qa)}
    preds = list(read_jsonl(args.predictions))
    if not preds:
        raise SystemExit('no predictions found')

    result = {}
    for k in ks:
        hits, precisions = [], []
        for row in preds:
            rel = qa.get(row['question_id'], set())
            top = row.get('retrieved_chunk_ids', [])[:k]
            hit_count = sum(1 for c in top if c in rel)
            hits.append(1 if hit_count > 0 else 0)
            precisions.append(hit_count / k)
        result[f'recall_at_{k}'] = round(mean(hits), 4)
        result[f'precision_at_{k}'] = round(mean(precisions), 4)

    rr = []
    for row in preds:
        rel = qa.get(row['question_id'], set())
        rank = 0
        for i, chunk_id in enumerate(row.get('retrieved_chunk_ids', []), start=1):
            if chunk_id in rel:
                rank = i
                break
        rr.append(1 / rank if rank else 0)
    result['mrr'] = round(mean(rr), 4)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()

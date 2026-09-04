"""
M1.4 — Chunking Strategy
Splits each cleaned historical bug record into overlapping text chunks
so long descriptions/stack traces/resolutions can be embedded properly.
Run this AFTER clean_data.py.
"""
import os
import json
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter

CLEAN_PATH = os.path.join(os.path.dirname(__file__), "data", "cleaned_historical_bugs.csv")
CHUNKS_PATH = os.path.join(os.path.dirname(__file__), "data", "bug_chunks.jsonl")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def build_chunk_text(row: pd.Series) -> str:
    parts = [
        f"Title: {row.get('title', '')}",
        f"Description: {row.get('description', '')}",
        f"Stack Trace: {row.get('stack_trace', '')}",
        f"Resolution: {row.get('resolution', '')}",
    ]
    return "\n".join(p for p in parts if p and not p.endswith(": "))


def chunk_dataset(input_path: str = CLEAN_PATH, output_path: str = CHUNKS_PATH):
    df = pd.read_csv(input_path)
    all_chunks = []

    for _, row in df.iterrows():
        full_text = build_chunk_text(row)
        pieces = splitter.split_text(full_text)

        for i, piece in enumerate(pieces):
            all_chunks.append({
                "chunk_id": f"{row['id']}_chunk{i}",
                "bug_id": row["id"],
                "source_repo": row.get("source_repo", "unknown"),
                "severity": row.get("severity", "unknown"),
                "status": row.get("status", "unknown"),
                "text": piece,
            })

    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk) + "\n")

    print(f"Created {len(all_chunks)} chunks from {len(df)} bug records -> {output_path}")
    return all_chunks


if __name__ == "__main__":
    chunk_dataset()
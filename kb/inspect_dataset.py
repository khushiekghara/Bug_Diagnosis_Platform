"""
Run this to inspect the actual DeepTriage dataset files (sev.csv, fix.csv, etc.)
"""
import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

CANDIDATE_FILES = [
    "sev.csv", "sev_train.csv", "sev_test.csv",
    "fix.csv", "fix_train.csv", "fix_test.csv",
]


def try_read(filename: str, nrows: int = 5):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"[skip] {filename} not found")
        return

    print(f"\n===== {filename} =====")
    try:
        df = pd.read_csv(path, nrows=nrows)
        print(f"Columns: {df.columns.tolist()}")
        print(df.head(nrows).to_string())
    except Exception as e:
        print(f"Failed as CSV ({e}) -- trying tab-separated...")
        try:
            df = pd.read_csv(path, sep="\t", nrows=nrows)
            print(f"Columns (tab-sep): {df.columns.tolist()}")
            print(df.head(nrows).to_string())
        except Exception as e2:
            print(f"Also failed as TSV ({e2}) -- showing raw first 500 chars:")
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                print(f.read(500))


if __name__ == "__main__":
    for fname in CANDIDATE_FILES:
        try_read(fname)
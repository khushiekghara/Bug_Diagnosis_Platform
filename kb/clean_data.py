"""
M1.4 -- Data Cleaning & Standardization
Reads fix.csv (columns: Unnamed: 0.2, Unnamed: 0, Unnamed: 0.1, Description,
Fixing_time, Label) and standardizes it into the schema the rest of the
pipeline (chunking.py, embeddings.py) expects:
id, source_repo, title, description, stack_trace, resolution, severity, status
"""
import pandas as pd
import re
import os

# Use the full fix.csv (fix_train.csv + fix_test.csv together make up this
# same dataset). Change this to fix_train.csv if fix.csv is too large to
# process quickly on your machine.
RAW_PATH = os.path.join(os.path.dirname(__file__), "data", "fix.csv")
CLEAN_PATH = os.path.join(os.path.dirname(__file__), "data", "cleaned_historical_bugs.csv")

# Cap how many rows we process -- the full file has tens of thousands of
# rows; for Milestone 1 a representative sample is enough and keeps
# embedding time reasonable. Set to None to process everything.
MAX_ROWS = 3000


def clean_text(text) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)          # collapse whitespace/newlines
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # strip stray non-ASCII noise
    return text


def make_title(description: str, max_len: int = 80) -> str:
    """Description has no separate title field -- derive a short one
    from the start of the cleaned text."""
    if not description:
        return "Untitled bug report"
    snippet = description[:max_len]
    return snippet + ("..." if len(description) > max_len else "")


def clean_dataset(input_path: str = RAW_PATH, output_path: str = CLEAN_PATH) -> pd.DataFrame:
    df = pd.read_csv(input_path, nrows=MAX_ROWS)

    df = df.rename(columns={"Unnamed: 0": "id", "Description": "description_raw"})

    df["description"] = df["description_raw"].apply(clean_text)
    df = df[df["description"].str.len() > 20]  # drop near-empty rows

    df["title"] = df["description"].apply(make_title)
    df["source_repo"] = "mozilla"        # this dataset's emails/URLs are mozilla.org / netscape.com
    df["stack_trace"] = ""               # not present in this dataset
    df["resolution"] = ""                # not present as a separate field
    df["severity"] = ""                  # not present in fix.csv (see sev.csv for that later)
    df["status"] = df["Label"].astype(str)

    df = df.drop_duplicates(subset=["id"])
    df = df.reset_index(drop=True)

    keep_cols = ["id", "source_repo", "title", "description", "stack_trace", "resolution", "severity", "status"]
    df = df[keep_cols]

    df.to_csv(output_path, index=False)
    print(f"Cleaned {len(df)} records -> {output_path}")
    return df


if __name__ == "__main__":
    clean_dataset()
"""
CIVIQ-AI: Training Dataset Builder and Quality Auditor
======================================================
1. Reads all CSVs in data/raw/, concatenates them, and validates columns:
   ['text', 'label', 'style', 'severity'].
2. Drops exact duplicates and near-duplicates (normalized text, TF-IDF cosine similarity > 0.9).
3. Removes rows with empty text or labels outside the 7 allowed categories:
   ['road', 'garbage', 'water', 'drainage', 'streetlight', 'electricity', 'other'].
4. Prints a comprehensive quality report:
   - Rows per category
   - Rows per style
   - Text-length statistics (character and word distributions)
   - Vocabulary size
   - Ratio of unique first-three-words (template repetition detector).
5. Saves the clean dataset to data/train.csv.
   (Explicitly ignores any file named test.csv).
"""

import os
import sys
import glob
import re
import string
import csv
import numpy as np
import pandas as pd
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Define Canonical 7 Allowed Categories
ALLOWED_CATEGORIES = {
    "road",
    "garbage",
    "water",
    "drainage",
    "streetlight",
    "electricity",
    "other"
}

# Synonyms/aliases normalized to the 7 canonical categories
CATEGORY_ALIASES = {
    "roads": "road",
    "pothole": "road",
    "potholes": "road",
    "sanitation": "garbage",
    "waste": "garbage",
    "solid_waste": "garbage",
    "drinking_water": "water",
    "water_supply": "water",
    "drain": "drainage",
    "drainages": "drainage",
    "sewer": "drainage",
    "sewerage": "drainage",
    "streetlights": "streetlight",
    "street_light": "streetlight",
    "street_lights": "streetlight",
    "lighting": "streetlight",
    "electrical": "electricity",
    "power": "electricity",
    "general": "other"
}

REQUIRED_COLUMNS = ["text", "label", "style", "severity"]

def normalize_text(text: str) -> str:
    """Normalize text by lowercasing, stripping punctuation, and collapsing whitespace."""
    if not isinstance(text, str):
        return ""
    # Lowercase
    t = text.lower()
    # Replace punctuation with spaces
    t = re.sub(r"[" + re.escape(string.punctuation) + r"]", " ", t)
    # Collapse multiple whitespace characters
    t = re.sub(r"\s+", " ", t).strip()
    return t

def get_first_three_words(text: str) -> str:
    """Extract normalized first three words of a complaint."""
    norm = normalize_text(text)
    words = norm.split()
    if len(words) >= 3:
        return " ".join(words[:3])
    elif len(words) > 0:
        return " ".join(words)
    return ""

def load_and_validate_raw_csvs(raw_dir: str) -> pd.DataFrame:
    """Read all CSVs in raw_dir (excluding test.csv) and validate column headers."""
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir, exist_ok=True)
        print(f"[*] Created missing directory: {raw_dir}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    # Explicitly filter out any file named test.csv
    valid_csvs = [
        f for f in csv_files 
        if os.path.basename(f).lower() != "test.csv"
    ]

    if not valid_csvs:
        print(f"[!] No input CSV files found in {raw_dir}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    dfs = []
    print(f"[*] Discovered {len(valid_csvs)} file(s) in {raw_dir}:")
    for filepath in sorted(valid_csvs):
        filename = os.path.basename(filepath)
        try:
            df_file = pd.read_csv(filepath, encoding="utf-8")
        except UnicodeDecodeError:
            df_file = pd.read_csv(filepath, encoding="latin1")

        # Validate required columns
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in df_file.columns]
        if missing_cols:
            raise ValueError(
                f"Validation Error in '{filename}': Missing required column(s) {missing_cols}. "
                f"Expected columns: {REQUIRED_COLUMNS}"
            )

        # Select only required columns (preserving extra metadata if needed, but standardizing)
        df_standard = df_file[REQUIRED_COLUMNS].copy()
        df_standard["_source_file"] = filename
        dfs.append(df_standard)
        print(f"    - {filename}: {len(df_standard)} rows loaded successfully")

    combined_df = pd.concat(dfs, ignore_index=True)
    return combined_df

def filter_invalid_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Filter out rows with empty text or invalid category labels."""
    initial_count = len(df)
    stats = {}

    # 1. Check for empty text
    df["_clean_text"] = df["text"].astype(str).str.strip()
    non_empty_mask = (df["_clean_text"] != "") & (df["_clean_text"].str.lower() != "nan")
    empty_text_dropped = initial_count - non_empty_mask.sum()
    df = df[non_empty_mask].copy()
    stats["empty_text_dropped"] = empty_text_dropped

    # 2. Normalize and check labels
    df["label"] = df["label"].astype(str).str.strip().str.lower()
    df["label"] = df["label"].map(lambda l: CATEGORY_ALIASES.get(l, l))

    valid_label_mask = df["label"].isin(ALLOWED_CATEGORIES)
    invalid_label_dropped = len(df) - valid_label_mask.sum()
    df = df[valid_label_mask].copy()
    stats["invalid_label_dropped"] = invalid_label_dropped

    return df, stats

def deduplicate_dataset(df: pd.DataFrame, sim_threshold: float = 0.9) -> tuple[pd.DataFrame, dict]:
    """Drop exact duplicates and near-duplicates based on TF-IDF cosine similarity."""
    initial_count = len(df)
    stats = {}

    # Step 1: Exact duplicate drop on normalized text
    df["_norm_text"] = df["text"].apply(normalize_text)
    
    # Filter any row where normalized text is empty
    df = df[df["_norm_text"].str.len() > 0].copy()

    df_exact = df.drop_duplicates(subset=["_norm_text"], keep="first").copy()
    exact_duplicates_dropped = initial_count - len(df_exact)
    stats["exact_duplicates_dropped"] = exact_duplicates_dropped

    if len(df_exact) <= 1:
        stats["near_duplicates_dropped"] = 0
        return df_exact, stats

    # Step 2: Near-duplicate detection using TF-IDF + Cosine Similarity
    norm_texts = df_exact["_norm_text"].tolist()
    vectorizer = TfidfVectorizer(ngram_range=(1, 1), min_df=1)
    tfidf_matrix = vectorizer.fit_transform(norm_texts)

    sim_matrix = cosine_similarity(tfidf_matrix)
    n = len(df_exact)

    to_drop_indices = set()
    for i in range(n):
        if i in to_drop_indices:
            continue
        # Find all subsequent items j > i with similarity > sim_threshold
        high_sim = np.where((sim_matrix[i] > sim_threshold) & (np.arange(n) > i))[0]
        for j in high_sim:
            to_drop_indices.add(j)

    near_duplicates_dropped = len(to_drop_indices)
    stats["near_duplicates_dropped"] = near_duplicates_dropped

    keep_mask = [idx not in to_drop_indices for idx in range(n)]
    df_deduped = df_exact.iloc[keep_mask].copy()

    return df_deduped, stats

def compute_quality_report(df: pd.DataFrame) -> dict:
    """Compute and print statistical metrics on the cleaned dataset."""
    total_rows = len(df)
    if total_rows == 0:
        return {"total_rows": 0}

    # 1. Rows per category
    cat_counts = df["label"].value_counts()

    # 2. Rows per style
    style_counts = df["style"].astype(str).str.strip().value_counts()

    # 3. Text length statistics
    char_lengths = df["text"].astype(str).str.len()
    word_lengths = df["text"].astype(str).apply(lambda t: len(t.split()))

    text_stats = {
        "char_min": int(char_lengths.min()),
        "char_max": int(char_lengths.max()),
        "char_mean": round(float(char_lengths.mean()), 2),
        "char_median": round(float(char_lengths.median()), 2),
        "word_min": int(word_lengths.min()),
        "word_max": int(word_lengths.max()),
        "word_mean": round(float(word_lengths.mean()), 2),
        "word_median": round(float(word_lengths.median()), 2),
    }

    # 4. Vocabulary size
    all_words = set()
    for text in df["text"].astype(str):
        words = normalize_text(text).split()
        all_words.update(words)
    vocab_size = len(all_words)

    # 5. Ratio of unique first-three-words (Template Repetition Detection)
    first_three_list = [
        get_first_three_words(t) 
        for t in df["text"].astype(str) 
        if get_first_three_words(t) != ""
    ]
    unique_first_three = len(set(first_three_list))
    total_prefixes = len(first_three_list)
    prefix_ratio = round(unique_first_three / total_prefixes, 4) if total_prefixes > 0 else 0.0

    report = {
        "total_rows": total_rows,
        "cat_counts": cat_counts,
        "style_counts": style_counts,
        "text_stats": text_stats,
        "vocab_size": vocab_size,
        "unique_prefixes": unique_first_three,
        "total_prefixes": total_prefixes,
        "prefix_ratio": prefix_ratio
    }
    return report

def print_report(report: dict, filter_stats: dict, dedup_stats: dict):
    """Print formatted terminal report."""
    print("\n" + "=" * 70)
    print("           CIVIQ-AI DATASET AUDIT & INGESTION REPORT           ")
    print("=" * 70)

    print("\n[1] CLEANING & DEDUPLICATION SUMMARY")
    print("-" * 50)
    print(f"  * Rows dropped (empty / whitespace text) : {filter_stats.get('empty_text_dropped', 0)}")
    print(f"  * Rows dropped (invalid category label)  : {filter_stats.get('invalid_label_dropped', 0)}")
    print(f"  * Exact duplicates dropped (normalized)  : {dedup_stats.get('exact_duplicates_dropped', 0)}")
    print(f"  * Near-duplicates dropped (cosine > 0.9) : {dedup_stats.get('near_duplicates_dropped', 0)}")
    print(f"  * Final Clean Training Rows              : {report.get('total_rows', 0)}")

    if report.get("total_rows", 0) == 0:
        print("\n[!] Dataset is empty after filtering. Exiting report.")
        print("=" * 70 + "\n")
        return

    print("\n[2] COMPLAINTS PER CATEGORY (7 Allowed Categories)")
    print("-" * 50)
    cat_counts = report["cat_counts"]
    for cat in sorted(ALLOWED_CATEGORIES):
        count = cat_counts.get(cat, 0)
        pct = round(count / report["total_rows"] * 100, 2)
        print(f"  * {cat:<15} : {count:>5} rows ({pct:>5.1f}%)")

    print("\n[3] COMPLAINTS PER WRITING STYLE")
    print("-" * 50)
    style_counts = report["style_counts"]
    for style, count in style_counts.items():
        pct = round(count / report["total_rows"] * 100, 2)
        print(f"  * {style:<15} : {count:>5} rows ({pct:>5.1f}%)")

    print("\n[4] TEXT-LENGTH STATISTICS")
    print("-" * 50)
    ts = report["text_stats"]
    print(f"  * Character Length -> Min: {ts['char_min']}, Max: {ts['char_max']}, Mean: {ts['char_mean']}, Median: {ts['char_median']}")
    print(f"  * Word Count       -> Min: {ts['word_min']}, Max: {ts['word_max']}, Mean: {ts['word_mean']}, Median: {ts['word_median']}")

    print("\n[5] VOCABULARY & TEMPLATE DIVERSITY METRICS")
    print("-" * 50)
    print(f"  * Total Unique Vocabulary Size          : {report['vocab_size']:,} unique words")
    print(f"  * Unique First-Three-Words Prefix Ratio : {report['prefix_ratio']:.4f} ({report['unique_prefixes']} unique / {report['total_prefixes']} total)")
    
    if report['prefix_ratio'] >= 0.75:
        diversity_status = "EXCELLENT (Diverse phrasing, natural variations, no template repetition)"
    elif report['prefix_ratio'] >= 0.50:
        diversity_status = "MODERATE (Some shared sentence openers detected)"
    else:
        diversity_status = "WARNING: HIGH REPETITION (Synthetic sentence template patterns detected)"
    print(f"  * Template Diversity Evaluation         : {diversity_status}")

    print("=" * 70 + "\n")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, "raw")
    train_out_path = os.path.join(base_dir, "train.csv")

    print("[*] Starting CIVIQ-AI dataset build pipeline...")
    raw_df = load_and_validate_raw_csvs(raw_dir)

    if len(raw_df) == 0:
        print("[!] No data available to process. Please place raw complaint CSVs in 'data/raw/'.")
        return

    # Filter invalid and empty rows
    filtered_df, filter_stats = filter_invalid_rows(raw_df)

    # Deduplicate exact and near duplicates (>0.9 cosine similarity)
    cleaned_df, dedup_stats = deduplicate_dataset(filtered_df, sim_threshold=0.9)

    # Generate and print statistical report
    report = compute_quality_report(cleaned_df)
    print_report(report, filter_stats, dedup_stats)

    # Save to data/train.csv (only required columns)
    export_df = cleaned_df[REQUIRED_COLUMNS].copy()
    export_df.to_csv(
        train_out_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_ALL
    )
    print(f"[OK] Saved {len(export_df)} verified training rows to: {train_out_path}")

if __name__ == "__main__":
    main()

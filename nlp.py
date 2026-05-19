"""Lightweight NLP helpers — keyword extraction and trending conditions."""
import re
from collections import Counter
import pandas as pd

# Hardcoded stopword list — no external NLP library needed
_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "to", "for", "with", "on",
    "at", "by", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would", "shall", "should",
    "may", "might", "can", "could", "not", "no", "nor", "so", "yet", "but",
    "from", "as", "up", "about", "into", "through", "during", "before",
    "after", "above", "below", "between", "each", "this", "that", "these",
    "those", "its", "it", "than", "then", "when", "where", "which", "who",
    "whom", "all", "both", "either", "neither", "other", "such", "only",
    "own", "same", "than", "too", "very", "just", "more", "most", "also",
    "study", "studies", "trial", "trials", "clinical", "patients", "patient",
    "disease", "treatment", "therapy", "randomized", "controlled", "phase",
    "versus", "vs", "use", "using", "used", "effect", "effects", "impact",
    "evaluation", "safety", "efficacy", "open", "label", "blinded", "double",
    "single", "multi", "pilot", "two", "three", "new", "based",
}


def extract_keywords(texts: list[str], top_n: int = 20) -> list[tuple[str, int]]:
    """Return the top_n most frequent meaningful words across all texts."""
    counter: Counter = Counter()
    for text in texts:
        if not text:
            continue
        words = re.findall(r"[a-z]{3,}", text.lower())
        for w in words:
            if w not in _STOPWORDS:
                counter[w] += 1
    return counter.most_common(top_n)


def get_trending_conditions(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Explode the conditions list column and return the top_n by occurrence count."""
    if df.empty or "conditions" not in df.columns:
        return pd.DataFrame(columns=["condition", "count"])
    try:
        # conditions column holds Python lists after get_trials() parsing
        exploded = df["conditions"].explode().dropna()
        exploded = exploded[exploded.str.strip() != ""]
        counts   = (
            exploded
            .str.strip()
            .str.title()
            .value_counts()
            .head(top_n)
            .reset_index()
        )
        counts.columns = ["condition", "count"]
        return counts
    except Exception as exc:
        print(f"[nlp] get_trending_conditions error: {exc}")
        return pd.DataFrame(columns=["condition", "count"])

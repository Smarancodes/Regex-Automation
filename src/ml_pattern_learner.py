"""
ml_pattern_learner.py
=====================
Learn regex patterns from PDF header/footer zones using:
    TF-IDF  →  KMeans clustering  →  keyword ranking  →  regex generation

No external API keys, no GPU.  Runs on standard office hardware.

Public API
----------
learn_patterns(pdf_paths, n_clusters=None)
    Full pipeline: extract zones → vectorise → cluster → generate regex.
    Returns  list of {"name": str, "regex": str}

save_patterns(patterns, json_path)
    Write learned patterns to patterns.json (same schema as the original).
"""

import json
import logging
import os
import re
import warnings

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

# Relative import from sibling within the same package
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.header_footer_extractor import extract_zones

logger = logging.getLogger(__name__)

# ── Tuneable constants ────────────────────────────────────────────────────────
MAX_FEATURES      = 500    # TF-IDF vocabulary cap
MIN_DF            = 1      # minimum document frequency for TF-IDF
MAX_KEYWORDS      = 6      # max keywords per cluster to put in regex
MIN_KEYWORD_LEN   = 3      # ignore very short tokens (articles, etc.)
MAX_CLUSTERS      = 10     # upper bound for auto-detect
MIN_CLUSTERS      = 2      # lower bound for auto-detect
RANDOM_STATE      = 42     # reproducibility


# ── Feature extraction ────────────────────────────────────────────────────────

def _build_corpus(zones: list[dict]) -> tuple[list[str], list[dict]]:
    """
    Combine header + footer text per page into a single document string.
    Drops pages where both header AND footer are empty.

    Returns
    -------
    corpus : list of str   — one entry per non-empty page
    kept   : list of dict  — corresponding zone dicts
    """
    corpus, kept = [], []
    for z in zones:
        combined = f"{z['header']} {z['footer']}".strip()
        if len(combined) >= 5:           # must have something useful
            corpus.append(combined)
            kept.append(z)
    return corpus, kept


def extract_features(corpus: list[str]):
    """
    Vectorise corpus with TF-IDF.

    Returns
    -------
    X            : np.ndarray  (n_samples, n_features)
    vectorizer   : fitted TfidfVectorizer (used later to get feature names)
    """
    if not corpus:
        raise ValueError("Corpus is empty — no usable header/footer text found in the PDFs.")

    vectorizer = TfidfVectorizer(
        max_features=MAX_FEATURES,
        min_df=MIN_DF,
        stop_words="english",
        ngram_range=(1, 2),     # unigrams + bigrams
        sublinear_tf=True,
    )
    X = vectorizer.fit_transform(corpus).toarray()
    logger.info("TF-IDF: %d documents × %d features", X.shape[0], X.shape[1])
    return X, vectorizer


# ── Clustering ────────────────────────────────────────────────────────────────

def _elbow_k(X: np.ndarray, max_k: int) -> int:
    """
    Pick the best k using the elbow heuristic (largest drop in inertia ratio).
    Falls back to sqrt(n_samples/2) heuristic if the curve is flat.
    """
    n = X.shape[0]
    max_k = min(max_k, n)          # can't have more clusters than samples
    if max_k <= MIN_CLUSTERS:
        return max_k

    inertias = []
    k_range = range(MIN_CLUSTERS, max_k + 1)
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        km.fit(X)
        inertias.append(km.inertia_)

    # Normalised second derivative ("elbow" = max curvature)
    drops = [inertias[i - 1] - inertias[i] for i in range(1, len(inertias))]
    best_idx = int(np.argmax(drops)) + 1   # +1 because drops are pairwise
    best_k = list(k_range)[best_idx]
    logger.info("Elbow method chose k=%d (inertias: %s)", best_k,
                [f"{v:.0f}" for v in inertias])
    return best_k


def cluster_pages(X: np.ndarray, n_clusters: int | None = None) -> tuple[np.ndarray, int]:
    """
    Cluster page feature vectors.

    Parameters
    ----------
    X          : TF-IDF matrix
    n_clusters : int or None — if None, automatically determined via elbow

    Returns
    -------
    labels     : np.ndarray of cluster ids per page
    k          : actual number of clusters used
    """
    n = X.shape[0]
    if n < 2:
        logger.warning("Only 1 document — cannot cluster, assigning everything to cluster 0.")
        return np.zeros(n, dtype=int), 1

    if n_clusters is None:
        k = _elbow_k(X, MAX_CLUSTERS)
    else:
        k = max(1, min(n_clusters, n))

    logger.info("Running KMeans with k=%d on %d documents …", k, n)
    km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        labels = km.fit_predict(X)

    for c in range(k):
        count = int((labels == c).sum())
        logger.info("  Cluster %d: %d page(s)", c, count)

    return labels, k


# ── Regex generation ──────────────────────────────────────────────────────────

def _top_keywords(cluster_id: int, labels: np.ndarray,
                  feature_names: list[str], X: np.ndarray,
                  top_n: int = MAX_KEYWORDS) -> list[str]:
    """
    Return the most discriminative keywords for a cluster by ranking
    the MEAN TF-IDF score of each feature across all cluster members.
    """
    mask = labels == cluster_id
    if not mask.any():
        return []

    mean_scores = X[mask].mean(axis=0)  # shape (n_features,)
    # Sort descending
    ranked = sorted(zip(mean_scores, feature_names), reverse=True)

    keywords = []
    seen = set()
    for score, kw in ranked:
        if score < 1e-6:
            break
        # Filter: min length, no pure digits, no duplicates
        if (len(kw) >= MIN_KEYWORD_LEN
                and not kw.isdigit()
                and kw not in seen):
            keywords.append(kw)
            seen.add(kw)
        if len(keywords) >= top_n:
            break

    return keywords


def _make_regex(keywords: list[str]) -> str:
    """
    Build a case-insensitive alternation regex from the keyword list.
    Multi-word bigrams use \\s+ between words (flexible spacing).

    Example: ["invoice number", "invoice", "bill to"]
        →  (?i)\\b(invoice\\s+number|invoice|bill\\s+to)\\b
    """
    if not keywords:
        return r"(?i)\b(unknown)\b"

    parts = []
    for kw in keywords:
        # escape, then allow flexible whitespace in bigrams
        escaped = re.escape(kw)
        escaped = escaped.replace(r"\ ", r"\s+")
        parts.append(escaped)

    return r"(?i)\b(" + "|".join(parts) + r")\b"


def generate_regex_for_cluster(
    cluster_id: int,
    labels: np.ndarray,
    feature_names: list[str],
    X: np.ndarray,
) -> str:
    """
    Generate a regex string for one cluster.
    """
    keywords = _top_keywords(cluster_id, labels, feature_names, X)
    pattern = _make_regex(keywords)
    logger.info("  Cluster %d keywords: %s", cluster_id, keywords)
    logger.info("  Cluster %d regex:    %s", cluster_id, pattern)
    return pattern


# ── Top-level API ─────────────────────────────────────────────────────────────

def learn_patterns(pdf_paths: list[str], n_clusters: int | None = None) -> list[dict]:
    """
    Full pipeline: PDF paths → list of learned {"name", "regex"} dicts.

    Parameters
    ----------
    pdf_paths  : paths to PDFs to learn from
    n_clusters : number of document types to discover (None = auto)

    Returns
    -------
    list of {"name": str, "regex": str}
        Names are "DocType_0", "DocType_1", … — rename in the JSON afterward.
    """
    logger.info("=== ML Pattern Learner ===")
    logger.info("Input PDFs: %s", [os.path.basename(p) for p in pdf_paths])

    # Step 1 — extract header/footer zones
    zones = extract_zones(pdf_paths)
    if not zones:
        raise RuntimeError("No zones extracted. Are the PDFs readable / non-empty?")

    # Step 2 — build corpus
    corpus, kept = _build_corpus(zones)
    logger.info("Corpus size after filtering: %d documents", len(corpus))
    if len(corpus) < 2:
        raise RuntimeError(
            "Not enough usable header/footer text found across the PDFs. "
            "Try PDFs that have visible headers or footers."
        )

    # Step 3 — TF-IDF vectorisation
    X, vectorizer = extract_features(corpus)
    feature_names = vectorizer.get_feature_names_out().tolist()

    # Step 4 — cluster
    labels, k = cluster_pages(X, n_clusters)

    # Step 5 — build regex per cluster
    patterns = []
    for c in range(k):
        name = f"DocType_{c}"
        regex = generate_regex_for_cluster(c, labels, feature_names, X)

        # Validate the regex compiles
        try:
            re.compile(regex)
        except re.error as exc:
            logger.warning("Generated invalid regex for cluster %d: %s — skipping", c, exc)
            continue

        patterns.append({"name": name, "regex": regex})

    logger.info("=== Learning complete — %d pattern(s) generated ===", len(patterns))
    return patterns


def save_patterns(patterns: list[dict], json_path: str) -> None:
    """
    Write learned patterns to patterns.json using the SAME schema as before.

    Schema:
        {"patterns": [{"name": str, "regex": str}, ...]}
    """
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    data = {"patterns": [{"name": p["name"], "regex": p["regex"]} for p in patterns]}

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info("Saved %d pattern(s) to: %s", len(patterns), json_path)


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from config.config import PATTERNS_FILE

    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s │ %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python src/ml_pattern_learner.py <file1.pdf> [file2.pdf ...]")
        sys.exit(1)

    pdf_paths = sys.argv[1:]
    patterns = learn_patterns(pdf_paths)

    print("\n" + "=" * 60)
    print("  LEARNED PATTERNS")
    print("=" * 60)
    for p in patterns:
        print(f"  {p['name']:20s}  →  {p['regex']}")
    print()

    save_patterns(patterns, PATTERNS_FILE)
    print(f"  Saved to: {PATTERNS_FILE}")
    print("  Tip: rename 'DocType_N' to a meaningful label in the JSON,")
    print("  then run: venv\\Scripts\\python src\\pipeline.py")

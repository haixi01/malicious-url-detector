"""
Feature extractor for the malicious URL detector.

This MUST match the feature extractor used to train the pickled Random Forest
(`rf_model.pkl`). Both the *set of feature names* and their *order* matter at
inference time — scikit-learn models expect columns in the exact order they
were trained on.

The notebook defines `extract_url_features` twice: a 12-feature version (used
to build `X_all_train`, which is what the RF is actually fit on) and a later
20-feature "Add more features" version that is defined but never used for
training. This file ships the 12-feature version so inference matches the
saved RF.

If you ever retrain with a different extractor:
  1. Update the function body below.
  2. Update FEATURE_COLUMNS to the new set and order.
  3. Replace `rf_model.pkl` with the newly trained model.
"""

import re
import numpy as np
import pandas as pd
from urllib.parse import urlparse


# The exact feature order used when training rf_model.pkl.
# Do not reorder. Do not add or remove entries without retraining.
FEATURE_COLUMNS = [
    "fe_url_length",
    "fe_num_special_chars",
    "fe_has_suspicious_token",
    "fe_digit_ratio",
    "fe_entropy",
    "fe_num_subdomains",
    "fe_is_ip",
    "fe_domain_length",
    "fe_hyphen_count",
    "fe_at_symbol",
    "fe_path_depth",
]

SUSPICIOUS_TOKENS = [
    "login", "verify", "secure", "account", "update", "confirm", "bank",
]


def extract_url_features(url: str) -> dict:
    """Extract engineered URL-only features from a single URL string.

    Returns a dict keyed by the names in FEATURE_COLUMNS.
    """
    url = str(url)
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    path = parsed.path or ""

    # --- Lexical ---
    length = len(url)
    num_special = sum(url.count(c) for c in ["@", "!", "$", "%", "#"])
    has_suspicious = int(any(t in url.lower() for t in SUSPICIOUS_TOKENS))
    digit_ratio = sum(c.isdigit() for c in url) / (length + 1)

    # --- Statistical (character-frequency entropy) ---
    if length > 0:
        char_freq = {c: url.count(c) / length for c in set(url)}
        entropy = -sum(f * np.log2(f) for f in char_freq.values() if f > 0)
    else:
        entropy = 0.0

    # --- Structural ---
    num_subdomains = hostname.count(".")
    is_ip = int(bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname)))
    domain_length = len(hostname)
    hyphen_count = hostname.count("-")
    at_symbol = int("@" in url)
    path_depth = path.count("/")

    return {
        "fe_url_length": length,
        "fe_num_special_chars": num_special,
        "fe_has_suspicious_token": has_suspicious,
        "fe_digit_ratio": digit_ratio,
        "fe_entropy": entropy,
        "fe_num_subdomains": num_subdomains,
        "fe_is_ip": is_ip,
        "fe_domain_length": domain_length,
        "fe_hyphen_count": hyphen_count,
        "fe_at_symbol": at_symbol,
        "fe_path_depth": path_depth,
    }


def features_to_frame(features: dict) -> pd.DataFrame:
    """Convert a feature dict to a 1-row DataFrame with columns in FEATURE_COLUMNS order."""
    row = [features[c] for c in FEATURE_COLUMNS]
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)
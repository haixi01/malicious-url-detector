"""
Streamlit app for the classroom malicious URL detector demo.

Run locally:
    streamlit run app.py

Expects `models/rf_model.pkl` — see README for how to produce it.
"""

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from feature_extractor import (
    FEATURE_COLUMNS,
    extract_url_features,
    features_to_frame,
)

MODEL_PATH = Path(__file__).parent / "models" / "rf_model.pkl"

# Edit these to change the quick-fill demo buttons.
DEMO_URLS = [
    "https://www.google.com",
    "http://secure-login.paypa1-verify-account.com/update",
    "http://192.168.0.14/bank/login?user=admin",
]

# Fallback label convention if the pkl is a bare model (no bundle metadata).
# The training notebook harmonizes labels so that 1 = malicious across both
# datasets, so that's the default assumption.
DEFAULT_MALICIOUS_CLASS = 1

st.set_page_config(
    page_title="Malicious URL Detector",
    page_icon="🔒",
    layout="centered",
)


@st.cache_resource
def load_model():
    """Load the model and its label convention from disk.

    Supports two pkl formats:
      1. New bundle format: {"model": rf, "malicious_class": 1, ...}
      2. Bare estimator: a raw RandomForestClassifier (assumes 1 = malicious)

    Returns (model, malicious_class) or (None, None) if the file is missing.
    """
    if not MODEL_PATH.exists():
        return None, None

    obj = joblib.load(MODEL_PATH)

    if isinstance(obj, dict) and "model" in obj:
        return obj["model"], int(obj.get("malicious_class", DEFAULT_MALICIOUS_CLASS))

    # Bare model — fall back to the convention from the training notebook.
    return obj, DEFAULT_MALICIOUS_CLASS


def predict(url: str, model, malicious_class: int):
    """Run a single-URL prediction. Returns (pred_label, malicious_probability, features_dict)."""
    features = extract_url_features(url)
    X = features_to_frame(features)

    pred = int(model.predict(X)[0])

    proba = None
    if hasattr(model, "predict_proba"):
        classes = list(model.classes_)
        if malicious_class in classes:
            proba = float(model.predict_proba(X)[0][classes.index(malicious_class)])

    return pred, proba, features


# --- UI ----------------------------------------------------------------------

st.title("🔒 Malicious URL Detector")
st.caption("Random Forest classifier trained on PhiUSIIL + a real-world URL dataset.")

st.warning(
    "⚠️ **Classroom demo model.** Held-out accuracy is ~89% and predictions "
    "may be imperfect. Do not use this for real security decisions."
)

model, malicious_class = load_model()
if model is None:
    st.error(
        f"Could not find `rf_model.pkl` at `{MODEL_PATH}`. "
        "See the README for how to train and save the model."
    )
    st.stop()

# Keep the URL text in session state so the demo buttons can pre-fill it.
if "url_input" not in st.session_state:
    st.session_state.url_input = ""

st.subheader("Try an example")
cols = st.columns(len(DEMO_URLS))
for col, demo in zip(cols, DEMO_URLS):
    with col:
        # `use_container_width` keeps the button layout tidy even with long URLs.
        if st.button(demo, use_container_width=True):
            st.session_state.url_input = demo

st.subheader("Or paste a URL")
url = st.text_input(
    "URL",
    key="url_input",
    placeholder="https://example.com/path?query=value",
    label_visibility="collapsed",
)

if url.strip():
    pred, proba, features = predict(url.strip(), model, malicious_class)

    label = "🔴 Malicious" if pred == malicious_class else "🟢 Benign"
    st.markdown(f"### Prediction: {label}")

    if proba is not None:
        st.metric("Malicious probability", f"{proba * 100:.1f}%")
        st.progress(min(max(proba, 0.0), 1.0))

    st.subheader("Extracted features")
    feature_df = pd.DataFrame(
        [(name, features[name]) for name in FEATURE_COLUMNS],
        columns=["feature", "value"],
    )
    st.dataframe(feature_df, hide_index=True, use_container_width=True)
else:
    st.info("Enter a URL above or click one of the example buttons.")
# Malicious URL Detector

A classroom demo that classifies URLs as **benign** or **malicious** using a Random Forest trained on URL-only engineered features (no webpage content required).

- **Model:** `sklearn.ensemble.RandomForestClassifier` (100 trees)
- **Features:** 12 engineered URL features (length, entropy, path depth, HTTPS, subdomains, suspicious tokens, …)
- **Training data:** PhiUSIIL Phishing URL Dataset + `url_data_mega_deep_learning.csv`
- **Held-out accuracy:** ~88.6%

> ⚠️ **Classroom demo only** — not suitable for real security decisions.

## Project layout

```
app.py                # Streamlit UI
feature_extractor.py  # Feature extractor + FEATURE_COLUMNS (inference order)
rf_model.pkl          # Trained Random Forest (you produce this — see below)
requirements.txt
Dockerfile
.gitignore
README.md
```

## 1. Save the trained model

In the Colab notebook, after `rf.fit(X_all_train, y_all_train)` has run, add a cell:

```python
import joblib
joblib.dump(rf, "rf_model.pkl")
```

Then download `rf_model.pkl` and place it next to `app.py`.

**Important:** the extractor in `feature_extractor.py` must match the one used to build `X_all_train`. This repo ships with the 12-feature version, which is what the RF at the end of the notebook is actually trained on. If you retrain with a different extractor:

1. Update `extract_url_features` in `feature_extractor.py`.
2. Update `FEATURE_COLUMNS` to the new names/order.
3. Replace `rf_model.pkl` with the newly trained model.

## 2. Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## 3. Deploy to Streamlit Community Cloud (free, optional)

1. Push this folder to a public GitHub repo. **Include `rf_model.pkl`** — it's under GitHub's 100 MB limit, so this usually just works.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, pick the repo and branch, and set `app.py` as the entry point.
4. Click **Deploy**. You get a public URL in ~1 minute.

If `rf_model.pkl` is too large for GitHub, host it with Git LFS or on Cloud Storage and download it on startup inside `app.py`.

## 4. Deploy to Google Cloud Run via Docker (optional)

Sanity-check the container locally first:

```bash
docker build -t url-detector .
docker run --rm -p 8501:8501 url-detector
# open http://localhost:8501
```

Then push and deploy:

```bash
# Substitute your GCP project id and preferred region.
export PROJECT_ID=your-gcp-project
export REGION=us-central1
export IMAGE=gcr.io/$PROJECT_ID/url-detector

gcloud auth configure-docker
docker build -t $IMAGE .
docker push $IMAGE

gcloud run deploy url-detector \
  --image=$IMAGE \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated
```

Cloud Run prints the public HTTPS URL when the deploy finishes. The container reads the `PORT` env var Cloud Run injects, so no extra config is needed.

## Editing tips

- **Change the demo URLs:** edit `DEMO_URLS` near the top of `app.py`.
- **Tweak the warning banner:** edit the `st.warning(...)` call in `app.py`.
- **Swap the extractor:** update `feature_extractor.py` (keep `FEATURE_COLUMNS` in sync with what the model was trained on) and replace `rf_model.pkl`.
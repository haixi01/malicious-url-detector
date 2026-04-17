# Malicious URL Detector

A classroom demo that classifies URLs as **benign** or **malicious** using a Random Forest trained on URL-only engineered features (no webpage content required).

- **Model:** `sklearn.ensemble.RandomForestClassifier` (100 trees)
- **Features:** 12 engineered URL features (length, entropy, path depth, HTTPS, subdomains, suspicious tokens, …)
- **Training data:** PhiUSIIL Phishing URL Dataset + `url_data_mega_deep_learning.csv`
- **Held-out accuracy:** ~88.6%
- **Live demo:** https://url-detector-157807866138.us-east1.run.app

> ⚠️ **Classroom demo only** — not suitable for real security decisions.

## Project layout

```
app.py                # Streamlit UI
feature_extractor.py  # Feature extractor + FEATURE_COLUMNS (inference order)
models/
  rf_model.pkl        # Trained Random Forest (you produce this — see below)
data/                 # Training CSVs (not needed at runtime)
malicious_url_detector.ipynb  # Training notebook
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

Download `rf_model.pkl` and place it at `models/rf_model.pkl` (create the `models/` directory if it doesn't exist). `app.py` loads from that path.

**Important:** the extractor in `feature_extractor.py` must match the one used to build `X_all_train`. This repo ships with the 12-feature version, which is what the RF at the end of the notebook is actually trained on. If you retrain with a different extractor:

1. Update `extract_url_features` in `feature_extractor.py`.
2. Update `FEATURE_COLUMNS` to the new names/order.
3. Replace `models/rf_model.pkl` with the newly trained model.

## 2. Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## 3. Deploy to Streamlit Community Cloud (optional)

1. Push this folder to a public GitHub repo. **Include `models/rf_model.pkl`** — it's under GitHub's 100 MB limit, so this usually just works.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, pick the repo and branch, and set `app.py` as the entry point.
4. Click **Deploy**. You get a public URL in ~1 minute.

If `models/rf_model.pkl` is too large for GitHub, host it with Git LFS or on Cloud Storage and download it on startup inside `app.py`.

## 4. Deploy to Google Cloud Run

Scales to zero when idle — a demo like this costs roughly pennies per month.

### Prerequisites

- `gcloud` CLI installed and logged in (`gcloud auth login`)
- Docker Desktop running locally
- A GCP billing account with a usable credit or payment method

> **Heads up on `.edu` accounts:** Google Workspace accounts (e.g. `*@andrew.cmu.edu`) often can't create new projects at the org level. If `gcloud projects create` returns `Permission 'resourcemanager.projects.create' denied on parent resource 'organizations/...'`, sign in with a personal Gmail instead:
> ```bash
> gcloud auth login              # pick a personal @gmail.com
> gcloud config set account <your>@gmail.com
> ```

### One-time setup

```bash
# Create a project (or reuse an existing one)
export PROJECT_ID=muml-demo-$(date +%s | tail -c 6)
gcloud projects create $PROJECT_ID --name="MUML Demo"
gcloud config set project $PROJECT_ID

# Link billing (pick an ACCOUNT_ID from `gcloud billing accounts list`)
gcloud billing projects link $PROJECT_ID --billing-account=XXXXXX-XXXXXX-XXXXXX

# Point Application Default Credentials at the new project
gcloud auth application-default login
gcloud auth application-default set-quota-project $PROJECT_ID

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# Create an Artifact Registry repo (gcr.io is deprecated)
export REGION=us-east1
export REPO=containers
export IMAGE=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/url-detector:latest

gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --description="Container images"

# Configure Docker to auth against Artifact Registry
gcloud auth configure-docker $REGION-docker.pkg.dev
```

### Sanity-check the container locally

```bash
docker build --platform linux/amd64 -t url-detector .
docker run --rm -p 8080:8080 -e PORT=8080 url-detector
# open http://localhost:8080
```

`--platform linux/amd64` is **required on Apple Silicon Macs** — Cloud Run runs amd64, and an arm64 image will push successfully but fail to start with a manifest error.

### Build, push, deploy

```bash
docker build --platform linux/amd64 -t $IMAGE .
docker push $IMAGE

gcloud run deploy url-detector \
  --image=$IMAGE \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --port=8080 \
  --min-instances=0 \
  --max-instances=3
```

Two non-obvious flags:
- `--memory=1Gi` — the default 512Mi will OOM when sklearn loads the Random Forest.
- `--min-instances=0` — pay nothing when idle (cold start ~3–5s).

Cloud Run prints the public HTTPS URL when the deploy finishes.

### Updating after code changes

```bash
docker build --platform linux/amd64 -t $IMAGE .
docker push $IMAGE
gcloud run deploy url-detector --image=$IMAGE --region=$REGION
```

### Tailing logs

```bash
gcloud run services logs tail url-detector --region=$REGION
```

### Locking it down later

`--allow-unauthenticated` makes the URL public. To revoke public access:

```bash
gcloud run services remove-iam-policy-binding url-detector \
  --region=$REGION \
  --member=allUsers \
  --role=roles/run.invoker
```

## Editing tips

- **Change the demo URLs:** edit `DEMO_URLS` near the top of `app.py`.
- **Tweak the warning banner:** edit the `st.warning(...)` call in `app.py`.
- **Swap the extractor:** update `feature_extractor.py` (keep `FEATURE_COLUMNS` in sync with what the model was trained on) and replace `models/rf_model.pkl`.
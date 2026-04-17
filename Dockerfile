FROM python:3.11-slim

WORKDIR /app

# Install deps first so the layer can be cached across code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code + trained model.
# NOTE: build will fail if rf_model.pkl is missing — put it here before `docker build`.
COPY app.py feature_extractor.py rf_model.pkl ./

# Streamlit's default port. Cloud Run overrides $PORT at runtime (usually 8080).
ENV PORT=8501
EXPOSE 8501

# Shell form so ${PORT} is expanded at container start, not build time.
CMD streamlit run app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
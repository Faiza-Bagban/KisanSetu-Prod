FROM python:3.11-slim

WORKDIR /app

# System dependencies needed by opencv, pytesseract, pdf2image
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-mar \
    tesseract-ocr-hin \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ../requirements.txt
COPY backend/requirements.txt ./requirements-backend.txt

# Install CPU-only torch first (avoids pulling ~2GB of unused CUDA packages
# inside the container — GPU passthrough isn't configured yet, so CUDA
# torch would be dead weight)
RUN pip install --no-cache-dir --default-timeout=120 torch==2.11.0 torchvision --index-url https://download.pytorch.org/whl/cpu



RUN pip install --no-cache-dir --default-timeout=120 --retries 5 -r ../requirements.txt \
    && pip install --no-cache-dir --default-timeout=120 --retries 5 -r requirements-backend.txt

RUN pip install --no-cache-dir --default-timeout=120 --force-reinstall torch==2.11.0 torchvision --index-url https://download.pytorch.org/whl/cpu

COPY backend/ .

# Pre-cache the zero-shot classifier model at build time (avoids slow
# first-request download/timeout)
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='valhalla/distilbart-mnli-12-1')"

# Train the lightweight grievance classifier at build time
RUN python -m modules.lightweight_classifier

EXPOSE 8000

# Render's Docker runtime injects a dynamic $PORT — bind to that instead
# of a hardcoded port
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
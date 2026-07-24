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

    

# COPY requirements.txt ../requirements.txt
# COPY backend/requirements.txt ./requirements-backend.txt

# RUN pip install --no-cache-dir --default-timeout=120 --retries 5 -r ../requirements.txt \
#     && pip install --no-cache-dir --default-timeout=120 --retries 5 -r requirements-backend.txt

COPY requirements.txt ../requirements.txt
COPY backend/requirements.txt ./requirements-backend.txt

# Install CPU-only torch first (avoids pulling ~2GB of unused CUDA packages
# inside the container — GPU passthrough isn't configured yet, so CUDA
# torch would be dead weight)
RUN pip install --no-cache-dir --default-timeout=120 torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir --default-timeout=120 --retries 5 -r ../requirements.txt \
    && pip install --no-cache-dir --default-timeout=120 --retries 5 -r requirements-backend.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
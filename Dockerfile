# PREVAIL backend image. Offline at runtime (SRS.md NFR): everything needed
# to serve inference is installed at build time; no outbound calls happen
# after the container starts (verified statically, see
# docs/architecture/offline-verification.md).
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir -e .

# Trained artifacts + demo dataset baked into the image so the container is
# usable standalone (no volume required for the SIH demo).
COPY artifacts/ artifacts/
COPY data/raw/synthetic_packets.csv data/raw/synthetic_packets.csv
COPY data/processed/states_w5s.parquet data/processed/states_w5s.parquet
COPY configs/ configs/

EXPOSE 8000
ENV PREVAIL_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

CMD ["uvicorn", "prevail.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

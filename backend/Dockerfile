FROM python:3.12-slim
ARG INSTALL_LOCAL=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr libjpeg62-turbo && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt requirements-local.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN if [ "$INSTALL_LOCAL" = "1" ]; then pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && grep -v '^torch' requirements-local.txt > /tmp/requirements-local-no-torch.txt && pip install --no-cache-dir -r /tmp/requirements-local-no-torch.txt; fi
COPY . .
CMD ["gunicorn", "config.wsgi", "-b", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]

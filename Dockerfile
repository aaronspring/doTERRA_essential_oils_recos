FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements first for better caching
COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade -r requirements.txt

# Copy entire app
COPY --chown=user . /app

# Expose port for HF Spaces
EXPOSE 7860

# Start backend on port 7860 (HF Spaces standard)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]

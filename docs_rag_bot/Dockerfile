# Use a modern Python image
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for pyOpenSSL, cryptography, and ChromaDB
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Ensure cli.py is in the current directory and executable
# (It's already in the root based on the COPY . . above)

# Use the full path for the entrypoint wrapper with shell expansion for $PORT
# We run from /app so server_rag:app is findable
CMD ["/bin/bash", "-c", "python3 cli.py gunicorn -b :$PORT server_rag:app -k uvicorn.workers.UvicornWorker --timeout 120"]

# Use Python 3.11 slim image as base
FROM public.ecr.aws/docker/library/python:3.11-slim

# Set work directory
WORKDIR /app

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install system dependencies (optional, adjust if any build deps needed)
RUN apt-get update && apt-get install -y curl bash g++ gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install uv && uv pip install -r requirements.txt

# Copy application code 
COPY . .


# Expose FastAPI port
EXPOSE 8000


RUN python presidio_entities.py

# Default command to run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Use the official Python slim image for a smaller footprint
FROM python:3.11-slim

# Set environment variables to optimize Python execution in Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# We install build-essential in case any python package (like lxml) needs to compile C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that the app runs on (Render uses the PORT env var)
EXPOSE $PORT

# Run the FastAPI application using Uvicorn
# We use sh -c to ensure the PORT environment variable is evaluated correctly at runtime
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]

# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY agent/ ./agent/
COPY data/ ./data/
COPY frontend/ ./frontend/
COPY presentation/ ./presentation/
COPY script/ ./script/

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose the port Cloud Run will use
EXPOSE 8080

# Run the application
CMD python app.py

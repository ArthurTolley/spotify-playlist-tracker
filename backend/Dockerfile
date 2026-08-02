# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies.
# --only-binary=:all: guarantees no compiler is needed; Flask-APScheduler is
# exempted because it only publishes a (pure-Python) source distribution.
RUN pip install --no-cache-dir --only-binary=:all:!Flask-APScheduler -r requirements.txt

# Copy application code
COPY . .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Create instance directory for SQLite (if needed for dev) and /data for the Docker volume
RUN mkdir -p instance /data

# Expose port
EXPOSE 8888

# Entrypoint initializes the database and starts the app
ENTRYPOINT ["/app/entrypoint.sh"]

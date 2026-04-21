# 1. Use a lightweight Python image
FROM python:3.12-slim

# 2. Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# 3. Set working directory
WORKDIR /app

# 4. Create a non-root user for security
# We'll call it 'appuser' to match your error logs
RUN addgroup --system appuser && \
    adduser --system --group appuser

# 5. Install dependencies
# We do this as root so we can write to the system-wide site-packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy project files
COPY . .

# 7. THE FIX: Create the instance folder and change ownership
# This MUST happen while we are still the root user
RUN mkdir -p /app/instance && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# 8. Switch to the non-root user for the rest of the execution
USER appuser

# 9. Start the application
# Using gunicorn as the production server
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "wsgi:app"
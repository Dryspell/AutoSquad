# AutoSquad Docker Image
FROM python:3.11-slim

# Set metadata
LABEL maintainer="AutoSquad Team <autosquad@example.com>"
LABEL description="AutoSquad - Autonomous Multi-Agent Development Framework"
LABEL version="0.1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.local/bin:$PATH"

# Create non-root user for security
RUN groupadd -r autosquad && useradd -r -g autosquad autosquad

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml setup.py ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir build

# Copy application code
COPY squad_runner/ ./squad_runner/
COPY __main__.py ./

# Install AutoSquad in the container
RUN pip install --no-cache-dir .

# Create directories for projects and logs
RUN mkdir -p /app/projects /app/logs \
    && chown -R autosquad:autosquad /app

# Switch to non-root user
USER autosquad

# Expose volume for projects
VOLUME ["/app/projects"]

# Set default command
CMD ["autosquad", "--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import squad_runner; print('AutoSquad is healthy')" || exit 1 
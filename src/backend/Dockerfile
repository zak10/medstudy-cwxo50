# Build stage
FROM python:3.11-slim AS builder

# Build arguments
ARG SECURITY_SCAN_VERSION=1.0.0

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies and security tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin v${SECURITY_SCAN_VERSION}

# Create app directory
WORKDIR /build

# Copy requirements file
COPY requirements.txt .

# Security scan dependencies
RUN grype requirements.txt --fail-on high

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Security scan application code
RUN grype . --fail-on high

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    APP_HOME=/app \
    DD_AGENT_HOST=datadog-agent \
    DD_TRACE_ENABLED=true \
    SECURITY_SCAN_ENABLED=true \
    APP_USER=appuser \
    APP_GROUP=appgroup

# Install production system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and group
RUN groupadd -r ${APP_GROUP} && \
    useradd -r -g ${APP_GROUP} -d ${APP_HOME} ${APP_USER}

# Create application directories
RUN mkdir -p ${APP_HOME}/static && \
    mkdir -p ${APP_HOME}/media && \
    mkdir -p ${APP_HOME}/logs && \
    mkdir -p /opt/datadog-agent/run

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY --chown=${APP_USER}:${APP_GROUP} . ${APP_HOME}

# Install monitoring agents
RUN curl -L https://dtdg.co/latest-dd-agent-script | DD_API_KEY=${DD_API_KEY} DD_SITE="us3.datadoghq.com" bash -s

# Copy scripts with correct permissions
COPY --chown=${APP_USER}:${APP_GROUP} scripts/entrypoint.sh /usr/local/bin/
COPY --chown=${APP_USER}:${APP_GROUP} scripts/wait-for-it.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/wait-for-it.sh

# Set up health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Set secure file permissions
RUN chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME} && \
    chmod -R 750 ${APP_HOME} && \
    chmod -R 770 ${APP_HOME}/media ${APP_HOME}/static ${APP_HOME}/logs

# Switch to non-root user
USER ${APP_USER}

# Set working directory
WORKDIR ${APP_HOME}

# Expose ports
EXPOSE 8000 8125 9090

# Set up volumes
VOLUME ["${APP_HOME}/static", "${APP_HOME}/media", "${APP_HOME}/logs", "/opt/datadog-agent/run"]

# Set entrypoint and default command
ENTRYPOINT ["entrypoint.sh"]
CMD ["api"]
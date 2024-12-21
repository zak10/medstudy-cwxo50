# Use official nginx alpine image for minimal footprint
FROM nginx:1.25-alpine

# Set environment variables
ENV NGINX_VERSION=1.25 \
    NODE_ENV=production

# Install required packages and clean up cache in single layer
RUN apk update && \
    apk add --no-cache curl && \
    rm -rf /var/cache/apk/* && \
    # Create nginx user if not exists
    adduser -D -S -h /var/cache/nginx -s /sbin/nologin -G nginx nginx || true && \
    # Create required directories with proper permissions
    mkdir -p /usr/share/nginx/html && \
    mkdir -p /var/cache/nginx && \
    mkdir -p /var/log/nginx && \
    # Set proper ownership and permissions
    chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chmod -R 755 /usr/share/nginx/html && \
    chmod -R 755 /var/cache/nginx && \
    chmod -R 755 /var/log/nginx && \
    # Remove default nginx configuration
    rm -rf /etc/nginx/conf.d/*

# Copy optimized nginx configuration
COPY --chown=nginx:nginx default.conf /etc/nginx/conf.d/default.conf

# Verify nginx configuration
RUN nginx -t

# Configure healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Switch to non-root user
USER nginx

# Expose HTTP port
EXPOSE 80

# Use exec form for more reliable signal handling
CMD ["nginx", "-g", "daemon off;"]

# Add labels for better container management
LABEL maintainer="Medical Research Platform Team" \
      version="1.0" \
      description="Nginx server for Vue.js frontend" \
      org.opencontainers.image.source="https://github.com/medical-research-platform" \
      org.opencontainers.image.vendor="Medical Research Platform" \
      org.opencontainers.image.title="Frontend Nginx Server" \
      org.opencontainers.image.description="Production Nginx server for serving Vue.js frontend application" \
      org.opencontainers.image.version="1.0" \
      org.opencontainers.image.created="2023-10-19"
# Bridge-MCP — hosted streamable-HTTP MCP server.
FROM python:3.11-slim

# Internal network proxy. Disable with --build-arg USE_PROXY=false.
ARG PROXY_URL=internal-proxy.snapp.tech
ARG PROXY_PORT=8118
ARG USE_PROXY=true

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    PORT=8080

COPY requirements.txt ./
RUN if [ "$USE_PROXY" = "true" ]; then \
        export http_proxy="http://$PROXY_URL:$PROXY_PORT" \
               https_proxy="http://$PROXY_URL:$PROXY_PORT" \
               HTTP_PROXY="http://$PROXY_URL:$PROXY_PORT" \
               HTTPS_PROXY="http://$PROXY_URL:$PROXY_PORT"; \
    fi && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8080

# OpenShift restricted-v2 overrides the UID with a random non-root one; site-packages
# stay world-readable and the app only writes to /tmp, so no explicit USER is needed.
CMD ["python", "/app/src/http_server.py"]

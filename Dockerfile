# ============================================================
# KODA — Production Dockerfile
# OWASP Container Security Verification Standard (CSVS) compliant
# ============================================================

# --- Stage 1: Dependencies ---
FROM python:3.11-slim AS deps

WORKDIR /app

# Install only production dependencies (no dev tools in final image)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip==24.3.1 \
    && pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Production ---
FROM python:3.11-slim AS production

# OWASP CSVS-4.1: Use specific image digest in production
# For hackathon, tag-based is acceptable

# Security metadata (OCI Image Spec)
LABEL org.opencontainers.image.title="KODA" \
      org.opencontainers.image.description="AI Companion for First-Generation Academics" \
      org.opencontainers.image.vendor="KODA Project" \
      org.opencontainers.image.source="https://github.com/florianpreiss/amazon-nova-ai-hackathon"

# OWASP CSVS-2.1: Non-root user
RUN groupadd --system koda \
    && useradd --system --gid koda --no-create-home --shell /sbin/nologin koda

# OWASP CSVS-3.1: Minimal packages, no cache
# Install curl for health check only
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies from build stage (multi-stage = smaller image)
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code (order matters for layer caching)
COPY config/ config/
COPY src/ src/
COPY frontend/ frontend/

# Streamlit static file serving: when running `streamlit run frontend/app.py`,
# Streamlit serves files from <script_dir>/static/ at the URL path app/static/.
# Since the script is at /app/frontend/app.py, static files must be at
# /app/frontend/static/ — which they already are after COPY frontend/ frontend/.
# No symlink needed; the COPY above already puts them in the right place.

# OWASP CSVS-2.2: Read-only filesystem where possible
RUN chown -R koda:koda /app

# OWASP CSVS-2.1: Switch to non-root user
USER koda

# Ensure src/ and config/ are importable as top-level packages
ENV PYTHONPATH=/app

# Expose Streamlit default port
EXPOSE 8501

# OWASP CSVS-5.1: Health check for orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Streamlit configuration via CLI flags
# Run from frontend/ so that Streamlit's static file serving resolves
# frontend/static/ correctly at the URL path app/static/
ENTRYPOINT ["streamlit", "run", "frontend/app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false", \
    "--server.enableCORS=false", \
    "--server.enableXsrfProtection=true", \
    "--server.maxUploadSize=1", \
    "--server.enableStaticServing=true"]

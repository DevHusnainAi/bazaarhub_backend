# ==================================================
# 🐳 AUTH SERVICE DOCKERFILE
# ==================================================
# Multi-stage build for small, secure production image
#
# ✅ BEST PRACTICES:
# 1. Multi-stage build (smaller final image ~100MB vs ~1GB)
# 2. Non-root user (security)
# 3. Pin Python version (reproducible builds)
# 4. Use uv for fast dependency installation

# --------------------------------------------------
# Stage 1: Builder
# --------------------------------------------------
FROM python:3.13-slim as builder

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files first (better layer caching)
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# --------------------------------------------------
# Stage 2: Production
# --------------------------------------------------
FROM python:3.13-slim as production

# ✅ BEST PRACTICE: Security - run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ✅ BEST PRACTICE: Switch to non-root user
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8001/health')" || exit 1

# Run the application
CMD ["uvicorn", "backend.services.auth.main:app", "--host", "0.0.0.0", "--port", "8001"]

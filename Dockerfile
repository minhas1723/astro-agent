# ==============================================================================
# Astro-Agent — Production Dockerfile
# Multi-stage build optimized for minimal image size
# ==============================================================================


# ── Stage 1: Build UI static files ───────────────────────────────────────────
FROM oven/bun:1-slim AS ui-builder

WORKDIR /build

# Layer cache optimization: install deps BEFORE copying source
# (deps change rarely, source changes often → cache hits on deps layer)
COPY ui/package.json ./
RUN bun install

# Copy UI source and build to static files
COPY ui/ .
RUN bun run build


# ── Stage 2: Install Python dependencies ─────────────────────────────────────
# Separate stage so we cache deps independently of source code changes
FROM python:3.12-slim AS deps

# Copy uv binary directly from their published image (no pip install needed)
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /bin/uv

WORKDIR /app

# Layer cache optimization: lock files first, source later
COPY api/pyproject.toml api/uv.lock ./

# Install deps into .venv with maximum optimization:
#   --frozen         : use exact versions from lock file
#   --no-dev         : skip dev dependencies
#   --no-install-project : don't install our own package (just deps)
#   --no-cache       : don't store uv cache (saves ~50MB)
#   --compile-bytecode : pre-compile .pyc files (faster cold start)
RUN uv sync \
    --frozen \
    --no-dev \
    --no-install-project \
    --no-cache \
    --compile-bytecode


# ── Stage 3: Final runtime image (minimal) ───────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN groupadd --system app && \
    useradd --system --gid app --home-dir /app --no-create-home app

WORKDIR /app

# Copy ONLY the virtual env from deps stage (contains all packages)
COPY --from=deps /app/.venv /app/.venv

# Put venv on PATH early so we can use it for the ONNX pre-cache step.
# Set HOME=/app so the model caches to /app/.cache/ (same path the app user sees at runtime).
ENV PATH="/app/.venv/bin:$PATH" \
    HOME=/app

# Pre-cache the ONNX embedding model (~80MB) into the image.
# Without this, ChromaDB downloads it from S3 on every container start.
RUN python -c "from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2; ONNXMiniLM_L6_V2()"

# Copy ONLY the required API source files
COPY api/main.py .
COPY api/src ./src

# Copy the knowledge base (JSON + TXT files for RAG indexing at startup)
COPY data/ ./data/

# Copy ONLY the built static files from UI stage (not source/node_modules)
COPY --from=ui-builder /build/dist ./static

# Create ChromaDB storage dir so the volume mount inherits app:app ownership
RUN mkdir -p /app/data/chroma_db

# Set file ownership (app user needs write access for ChromaDB in data/)
RUN chown -R app:app /app

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root
USER app

EXPOSE 4219

# Health check using Python (no curl/wget needed → smaller image)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:4219/health')"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4219", "--workers", "1", "--no-access-log"]

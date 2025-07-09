# BioAlgoCompare Development Environment
# Multi-stage build for optimal size and security

# Base stage with Python and system dependencies
FROM python:3.9-slim-bullseye AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry for dependency management
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Development stage with all tools
FROM base AS development

# Set working directory
WORKDIR /workspace

# Copy dependency files first (better caching)
COPY pyproject.toml poetry.lock* requirements*.txt ./

# Install dependencies
RUN if [ -f poetry.lock ]; then \
        poetry install --no-root; \
    elif [ -f requirements.txt ]; then \
        pip install -r requirements.txt; \
    else \
        echo "No dependency file found"; \
    fi

# Install development tools
RUN pip install \
    ruff \
    mypy \
    pytest \
    pytest-cov \
    pytest-xdist \
    bandit \
    pre-commit \
    ipython \
    jupyter \
    notebook \
    jupyterlab \
    matplotlib \
    seaborn \
    plotly \
    && pre-commit install --install-hooks

# Copy project files
COPY . .

# Install project in editable mode
RUN pip install -e .

# Create non-root user for security
RUN useradd -m -s /bin/bash developer && \
    chown -R developer:developer /workspace

# Switch to non-root user
USER developer

# Set up shell
RUN echo 'alias ll="ls -la"' >> ~/.bashrc && \
    echo 'alias bioalgo="python scripts/cli/main.py"' >> ~/.bashrc && \
    echo 'export PS1="\[\033[36m\]\u\[\033[m\]@\[\033[32m\]bioalgo:\[\033[33;1m\]\w\[\033[m\]$ "' >> ~/.bashrc

# Expose ports for Jupyter
EXPOSE 8888 8889

# Default command
CMD ["/bin/bash"]

# Production stage (minimal)
FROM base AS production

WORKDIR /app

# Copy only necessary files
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY algorithms algorithms/
COPY problems problems/
COPY utils utils/
COPY scripts scripts/
COPY data data/
COPY setup.py ./

# Install in production mode
RUN pip install .

# Create non-root user
RUN useradd -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Run with minimal command
ENTRYPOINT ["python", "-m", "scripts.cli.main"]

# Test stage for CI/CD
FROM development AS testing

USER root

# Install additional test dependencies
RUN pip install \
    pytest-parallel \
    pytest-timeout \
    pytest-mock \
    hypothesis

# Copy test files
COPY tests tests/
COPY .coveragerc pytest.ini ./

# Switch back to developer user
USER developer

# Run tests by default
CMD ["pytest", "-v", "--cov=algorithms", "--cov=problems", "--cov=utils"]
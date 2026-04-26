# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Place the virtual environment outside the mounted source tree
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project into `/app`
WORKDIR /app

# First, install the dependencies without the project
# This step is cached as long as uv.lock and pyproject.toml don't change
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Now, copy the project source code
COPY . /app

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Start the application
CMD ["uv", "run", "uvicorn", "deleprep.main:app", "--host", "0.0.0.0", "--port", "8000"]

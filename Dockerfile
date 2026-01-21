FROM python:3.13-slim-bookworm

# Copy uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

COPY . .

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Disable development dependencies
ENV UV_NO_DEV=1

# Install dependencies
RUN uv sync --locked


# Expose the port
EXPOSE 8000

# Run the application using the venv explicitly
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application
COPY . .
RUN uv sync --locked

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["uv", "run", "main.py"]
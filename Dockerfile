FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies without dev tools
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy source code
COPY src ./src

# Expose port
EXPOSE 8000

# Run application
COPY start.sh ./script/start.sh
RUN chmod +x start.sh

CMD ["./script/start.sh"]
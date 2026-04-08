FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install uv
RUN pip install uv

# copy dependency files first (for caching)
COPY pyproject.toml uv.lock ./

# install deps
RUN uv sync --frozen

# copy rest of code
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
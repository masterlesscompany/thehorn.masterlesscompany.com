# 백엔드 이미지. Fake 모델만으로도 완주하므로 자격증명 없이 뜬다.
FROM python:3.12-slim

WORKDIR /app

# uv 로 잠금 파일 그대로 설치한다. --frozen 이 없으면 매 빌드가 의존성을 다시
# 해결해서, 초록불이 잠금 파일을 보증하지 않게 된다.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY apps/ apps/
COPY core/ core/
COPY content/ content/
COPY eval/ eval/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    RPG_MODEL=fake \
    RPG_RUNS_DIR=/data/runs \
    RPG_EXPERIMENTS_DIR=/app/eval/out

# 런 기록은 컨테이너 밖에 둔다. 재시작해도 완료된 판을 다시 열 수 있어야 한다.
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/healthz').status==200 else 1)"

CMD ["uvicorn", "apps.arena.adapter.inbound.api.v1.arena_router:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

cwd := `pwd`
mypy := "uv run mypy"
python := "uv run python"
pytest := "uv run pytest"
ruff := "uv run ruff"

test:
    {{ pytest }}

lint:
    {{ ruff }} check .

types:
    {{ mypy }} src

check: lint types

coverage:
    {{ pytest }} --cov

db:
    PYTHONPATH=src {{ python }} -m rgb_logseq.db

publish:
    PYTHONPATH=src {{ python }} -m rgb_logseq.publisher

explore:
    docker run -p 8000:8000 \
      -v ./graph_db:/database \
      -e MODE=READ_ONLY \
      --rm kuzudb/explorer:0.8.0

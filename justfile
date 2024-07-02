cwd := `pwd`
mypy := ".venv/Scripts/mypy"
python := ".venv/Scripts/python"
pytest := ".venv/Scripts/pytest"
ruff := ".venv/Scripts/ruff"

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
      -v e:/proj/rgb-logseq-toolkit/graph_db:/database \
      -e MODE=READ_ONLY \
      --rm kuzudb/explorer:latest

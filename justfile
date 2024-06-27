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

db: clean-db
    PYTHONPATH=src {{ python }} -m rgb_logseq.db

clean-db:
  if [ -d graph_db ]; then rm -r graph_db; fi

explore:
    docker run -p 8000:8000 \
      -v {{ cwd }}/graph_db:/database \
      -e MODE=READ_ONLY \
      --rm kuzudb/explorer:latest

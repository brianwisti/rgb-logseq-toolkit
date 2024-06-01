cwd := `pwd`

test:
    pdm run pytest

lint:
    pdm run ruff check .

types:
    pdm run mypy

check: lint types

db: clean-db
    PYTHONPATH=src pdm run python -m rgb_logseq.db

clean-db:
  if [ -d graph_db ]; then rm -r graph_db; fi

explore:
    docker run -p 8000:8000 \
      -v {{ cwd }}/graph_db:/database \
      --rm kuzudb/explorer:latest

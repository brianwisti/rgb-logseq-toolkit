"""Explore my Logseq graph in Kuzu."""

from pathlib import Path
import os

from dotenv import load_dotenv
import kuzu
import polars

from .const import logger
from .graph import Graph
from .page import load_page_file

PAGE_SCHEMA = """
    create node table Page(
        name string,
        is_placeholder boolean,
        primary key (name)
    )
"""

LINKS_SCHEMA = """
    create rel table Links(
        from Page
        to Page
    )
"""

load_dotenv()


def load_graph(graph_path: Path) -> Graph:
    """Load pages in Graph."""
    logger.info("path: %s", graph_path)
    graph = Graph()
    page_folders = ["journals", "pages"]

    for folder in page_folders:
        subfolder = graph_path / folder
        for md_path in subfolder.glob("./**/*.md"):
            logger.debug("md path: %s", md_path)
            page = load_page_file(md_path)
            logger.debug("page: %s", page)
            graph.add_page(page)

    return graph


def create_db() -> kuzu.Connection:
    db = kuzu.Database("./graph_db")
    conn = kuzu.Connection(db)
    conn.execute(PAGE_SCHEMA)
    conn.execute(LINKS_SCHEMA)

    return conn


def main() -> None:
    """Do interesting stuff."""
    graph_path = os.getenv("GRAPH_PATH")
    assert graph_path

    pages_path = Path(graph_path).expanduser()
    graph = load_graph(pages_path)
    graph_name = pages_path.stem
    logger.info("Loaded graph %s; %s pages", graph_name, len(graph.pages))
    # TODO: refactor page listing to Graph method
    pages = [
        {"name": page.name, "is_placeholder": page.is_placeholder}
        for page in graph.pages.values()
    ]
    links = graph.links
    polars.DataFrame(pages).write_csv("page.csv", include_header=False)
    polars.DataFrame(links).write_csv("links.csv", include_header=False)
    conn = create_db()
    conn.execute('COPY Page from "page.csv"')
    conn.execute('COPY Links from "links.csv"')


if __name__ == "__main__":
    main()

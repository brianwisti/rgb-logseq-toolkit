"""Explore my Logseq graph in Kuzu."""

from pathlib import Path
import os

from dotenv import load_dotenv
import kuzu
import pandas as pd

from .const import logger
from .graph import Graph, load_graph
from .page import NAMESPACE_SELF

GRAPH_PATH_ENV = "GRAPH_PATH"

DB_NAME = "graph_db"
DB_SCHEMA_PATH = Path("etc/schema.cypher")

load_dotenv()


def create_db(db_name: str, schema_path: Path) -> kuzu.Connection:
    """Create the database for our Logseq graph and return a connection."""
    db = kuzu.Database(db_name)
    conn = kuzu.Connection(db)
    schema = schema_path.read_text(encoding="utf-8")
    conn.execute(schema)

    return conn


def load_graph_blocks(graph: Graph) -> dict[str, pd.DataFrame]:
    """Load block info from the graph."""
    blocks = []
    links = []
    page_memberships = []
    block_properties = []

    for page_name, page in graph.pages.items():
        for position, block_info in enumerate(page.blocks):
            blocks.append(
                {
                    "uuid": str(block_info.id),
                    "content": block_info.content,
                    "is_heading": block_info.is_heading,
                    "directive": block_info.directive,
                }
            )
            page_memberships.append(
                {
                    "block": str(block_info.id),
                    "page": page_name,
                    "position": position,
                    "depth": block_info.depth,
                }
            )

            for link in block_info.links:
                links.append({"source": str(block_info.id), "target": link.target})

            for prop_name, prop in block_info.properties.items():
                block_properties.append(
                    {
                        "block": str(block_info.id),
                        "prop": prop_name,
                        "value": prop.value,
                    }
                )

    return {
        "blocks": pd.DataFrame(blocks),
        "links": pd.DataFrame(links),
        "page_memberships": pd.DataFrame(page_memberships),
        "block_properties": pd.DataFrame(block_properties),
    }


def load_graph_pages(graph: Graph) -> dict[str, pd.DataFrame]:
    """Load page info from the graph."""
    pages = []
    namespaces = []
    page_properties = []
    tags = []

    for page in graph.pages.values():
        pages.append(
            {
                "name": page.name,
                "is_placeholder": page.is_placeholder,
                "is_public": page.is_public,
            }
        )

        if page.namespace != NAMESPACE_SELF:
            namespaces.append({"page": page.name, "namespace": page.namespace})

        for tag in page.tags:
            tags.append({"page": page.name, "tag": tag})

        for prop_name, page_prop in page.properties.items():
            page_properties.append(
                {
                    "page": page.name,
                    "property": prop_name,
                    "value": page_prop.value,
                }
            )

    return {
        "pages": pd.DataFrame(pages),
        "namespaces": pd.DataFrame(namespaces),
        "page_properties": pd.DataFrame(page_properties),
        "tags": pd.DataFrame(tags),
    }


def save_graph_blocks(graph: Graph, conn: kuzu.Connection) -> None:
    """Store Blocks and their Page connections in CSV files."""
    graph_block_info = load_graph_blocks(graph)

    blocks = graph_block_info["blocks"]
    logger.info("Saving %s blocks", len(blocks))
    conn.execute(
        """
            COPY Block FROM (
                LOAD FROM blocks
                RETURN cast(uuid, 'UUID'), content, is_heading, directive
            )
        """
    )

    links = graph_block_info["links"]
    logger.info("Saving %s direct links", len(links))
    conn.execute(
        """
            COPY Links FROM (
                LOAD FROM links
                RETURN cast(source, 'UUID'), target
            )
        """
    )

    block_properties = graph_block_info["block_properties"]
    logger.info("Saving %s block properties", len(block_properties))
    conn.execute(
        """
            COPY BlockHasProperty FROM (
                LOAD FROM block_properties
                RETURN cast(block, 'UUID'), prop, value
            )
        """
    )

    page_memberships = graph_block_info["page_memberships"]
    logger.info("Saving %s page memberships", len(page_memberships))
    conn.execute(
        """
        COPY InPage FROM (
            LOAD FROM page_memberships
            RETURN cast(block, 'UUID'), page, position, depth
        )
        """
    )

    logger.info("Finished saving block data.")


def save_graph_pages(graph: Graph, conn: kuzu.Connection) -> None:
    """Store page info from graph in a CSV file."""
    page_data = load_graph_pages(graph)

    pages = page_data["pages"]
    logger.info("Saving %s pages", len(pages))
    conn.execute("COPY Page FROM (LOAD FROM pages RETURN *)")

    namespaces = page_data["namespaces"]
    logger.info("Saving %s namespaces", len(namespaces))
    conn.execute("COPY InNamespace FROM (LOAD FROM namespaces RETURN *)")

    page_properties = page_data["page_properties"]
    logger.info("Saving %s page properties", len(page_properties))
    conn.execute("COPY PageHasProperty FROM (LOAD FROM page_properties RETURN *)")

    tags = page_data["tags"]
    logger.info("Saving %s tags", len(tags))
    conn.execute("COPY PageIsTagged FROM (LOAD FROM tags RETURN *)")

    logger.info("Database populated with page data.")


def main() -> None:
    """Do interesting stuff."""
    graph_path = os.getenv(GRAPH_PATH_ENV)
    assert graph_path

    pages_path = Path(graph_path).expanduser()
    graph = load_graph(pages_path)
    logger.info("Loaded graph %s; %s pages", pages_path.stem, len(graph.pages))
    conn = create_db(DB_NAME, DB_SCHEMA_PATH)
    save_graph_pages(graph, conn)
    save_graph_blocks(graph, conn)


if __name__ == "__main__":
    main()

"""Explore my Logseq graph in Kuzu."""

from pathlib import Path
from typing import Any
import os

from dotenv import load_dotenv
import kuzu
import polars


from .const import logger
from .graph import Graph, load_graph
from .page import NAMESPACE_SELF

GRAPH_PATH_ENV = "GRAPH_PATH"

DB_NAME = "graph_db"
DB_SCHEMA_PATH = Path("etc/schema.cypher")

TABLE_NAMES = [
    "Page",
    "Block",
    "InPage",
    "Links",
    "InNamespace",
    "PageIsTagged",
    "PageHasProperty",
    "BlockHasProperty",
]

CSV_FOR = {name: f"stash/{name}.csv" for name in TABLE_NAMES}

load_dotenv()


def create_db(db_name: str, schema_path: Path) -> kuzu.Connection:
    """Create the database for our Logseq graph and return a connection."""
    db = kuzu.Database(db_name)
    conn = kuzu.Connection(db)
    schema = schema_path.read_text(encoding="utf-8")
    conn.execute(schema)

    return conn


def populate_database(conn: kuzu.Connection) -> None:
    """Copy graph info from CSV files to database."""
    # XXX: Does parameter binding not work for COPY?
    commands = [f'COPY {table} FROM "{CSV_FOR[table]}";' for table in TABLE_NAMES]
    full_command = "\n".join(commands)
    conn.execute(full_command)


def prepare_text(text: str) -> str:
    """
    Reformat text so that Kuzu can handle it.

    Primarily used in CSV generation.
    """
    return (
        text.replace("\\$", "$")
        .replace("\\", "\\\\")
        .replace("\n", "\\\\n")
        .replace('"', "*")
    )


RowInfo = dict[str, Any]
RowInfoList = list[RowInfo]


def load_graph_blocks(graph: Graph) -> dict[str, RowInfoList]:
    """Load block info from the graph."""
    blocks = []
    page_memberships = []
    block_properties = []

    for page_name, page in graph.pages.items():
        for position, block_info in enumerate(page.blocks):
            blocks.append(
                {
                    "uuid": block_info.id,
                    "content": block_info.content,
                    "is_heading": block_info.is_heading,
                    "directive": block_info.directive,
                }
            )
            page_memberships.append(
                {
                    "block": block_info.id,
                    "page": page_name,
                    "position": position,
                    "depth": block_info.depth,
                }
            )

            for prop_name, prop in block_info.properties.items():
                block_properties.append(
                    {
                        "block": block_info.id,
                        "prop": prop_name,
                        "value": prop.value,
                    }
                )

    return {
        "blocks": blocks,
        "page_memberships": page_memberships,
        "block_properties": block_properties,
    }


def load_graph_pages(graph: Graph) -> dict[str, RowInfoList]:
    """Load page info from the graph."""
    pages = []
    namespaces = []
    page_properties = []
    links = []
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

        for link in page.links:
            links.append({"source": page.name, "target": link.target})

        for tag in page.tags:
            tags.append({"page": page.name, "tag": tag})

        for prop_name, page_prop in page.properties.items():
            page_properties.append(
                {
                    "page": page.name,
                    "property": prop_name,
                    "value": prepare_text(page_prop.value),
                }
            )

    return {
        "pages": pages,
        "namespaces": namespaces,
        "page_properties": page_properties,
        "links": links,
        "tags": tags,
    }


def save_graph_blocks(graph: Graph, conn: kuzu.Connection) -> None:
    """Store Blocks and their Page connections in CSV files."""
    graph_block_info = load_graph_blocks(graph)

    blocks = graph_block_info["blocks"]
    logger.info("Saving %s blocks", len(blocks))
    conn.execute("BEGIN TRANSACTION;")

    for block_info in blocks:
        conn.execute(
            """
                CREATE (
                    b:Block {
                        uuid: $uuid,
                        content: $content,
                        is_heading: $is_heading,
                        directive: $directive
                    }
                );
            """,
            block_info,
        )

    conn.execute("COMMIT;")
    block_properties = graph_block_info["block_properties"]
    logger.info("Saving %s block properties", len(block_properties))
    conn.execute("BEGIN TRANSACTION;")

    for prop in block_properties:
        conn.execute(
            """
                MATCH (b:Block {uuid: $block}), (p:Page {name: $prop})
                CREATE (b)-[:BlockHasProperty {value: $value}]->(p);
            """,
            prop,
        )

    page_memberships = graph_block_info["page_memberships"]
    logger.info("Saving %s page memberships", len(page_memberships))
    for membership in page_memberships:
        conn.execute(
            """
                MATCH (b:Block {uuid: $block}), (p:Page {name: $page})
                CREATE (b)-[:InPage {position: $position, depth: $depth}]->(p);
            """,
            membership,
        )
    conn.execute("COMMIT;")

    logger.info("Finished saving block data.")


def save_graph_pages(graph: Graph, conn: kuzu.Connection) -> None:
    """Store page info from graph in a CSV file."""
    page_data = load_graph_pages(graph)

    pages = page_data["pages"]
    logger.info("Saving %s pages", len(pages))
    conn.execute("BEGIN TRANSACTION;")  # Start a transaction.
    page_st = conn.prepare(
        """
            CREATE (
                p:Page {
                    name: $name,
                    is_placeholder: $is_placeholder,
                    is_public: $is_public
                }
            );
        """
    )
    for page_info in pages:
        conn.execute(page_st, page_info)
    conn.execute("COMMIT;")  # Commit the transaction.

    namespaces = page_data["namespaces"]
    logger.info("Saving %s namespaces", len(namespaces))
    conn.execute("BEGIN TRANSACTION;")  # Start a transaction.
    namespace_st = conn.prepare(
        """
            MATCH (p:Page {name: $page}), (n:Page {name: $namespace})
            CREATE (p)-[:InNamespace]->(n);
        """
    )
    for namespace in namespaces:
        # Create a namespace relation for each saved namespace.
        logger.debug("Creating namespace relation: %s", namespace)
        conn.execute(namespace_st, namespace)

    page_properties = page_data["page_properties"]
    logger.info("Saving %s page properties", len(page_properties))
    page_prop_st = conn.prepare(
        """
            MATCH (p:Page {name: $page}), (pr:Page {name: $property})
            CREATE (p)-[:PageHasProperty {value: $value}]->(pr);
        """
    )

    for page_prop in page_properties:
        # Create a property relation for each saved property.
        logger.debug("Creating page property relation: %s", page_prop)
        conn.execute(page_prop_st, page_prop)

    links = page_data["links"]
    logger.info("Saving %s links", len(links))
    for link in links:
        # Create a link relation for each saved link.
        logger.debug("Creating link relation: %s", link)
        conn.execute(
            """
                MATCH (s:Page {name: $source}), (t:Page {name: $target})
                CREATE (s)-[:Links]->(t);
            """,
            link,
        )

    tags = page_data["tags"]
    logger.info("Saving %s tags", len(tags))
    for tag in tags:
        # Create a tag relation for each saved tag.
        logger.debug("Creating tag relation: %s", tag)
        conn.execute(
            """
                MATCH (p:Page {name: $page}), (t:Page {name: $tag})
                CREATE (p)-[:PageIsTagged]->(t);
            """,
            tag,
        )

    conn.execute("COMMIT;")  # Commit the transaction.
    logger.info("Database populated with page data.")


def write_as_csv(df: polars.DataFrame, table: str) -> None:
    """Write a DataFrame as CSV to the specified file."""
    df.write_csv(CSV_FOR[table], include_header=False, quote_style="non_numeric")


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

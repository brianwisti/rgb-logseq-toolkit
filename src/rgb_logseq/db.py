"""Explore my Logseq graph in Kuzu."""

from pathlib import Path
import os

from dotenv import load_dotenv
import kuzu
import polars

from .const import logger
from .graph import Graph
from .page import NAMESPACE_SELF, load_page_file

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


def load_graph(graph_path: Path) -> Graph:
    """Load pages in Graph."""
    logger.info("path: %s", graph_path)
    page_folders = ["journals", "pages"]
    page_glob = "./**/*.md"
    graph = Graph()

    for folder in page_folders:
        subfolder = graph_path / folder
        for md_path in subfolder.glob(page_glob):
            logger.debug("md path: %s", md_path)
            page = load_page_file(md_path)
            logger.debug("page: %s", page)
            graph.add_page(page)

    return graph


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


def save_graph_blocks(graph: Graph) -> None:
    """Store Blocks and their Page connections in CSV files."""
    blocks = []
    in_page = []
    block_properties = []

    for page_name, page in graph.pages.items():
        for position, block in enumerate(page.blocks):
            content = prepare_text(block.content)
            blocks.append(
                {
                    "uuid": block.id,
                    "content": content,
                    "is_heading": block.is_heading,
                    "directive": block.directive,
                }
            )
            in_page.append(
                {
                    "from": block.id,
                    "to": page_name,
                    "position": position,
                    "depth": block.depth,
                }
            )

            for prop_name, prop in block.properties.items():
                block_properties.append(
                    {
                        "from": block.id,
                        "to": prop_name,
                        "value": prepare_text(prop.value),
                    }
                )

    blocks_df = polars.DataFrame(blocks)
    in_page_df = polars.DataFrame(in_page)
    block_properties_df = polars.DataFrame(block_properties)
    write_as_csv(blocks_df, "Block")
    write_as_csv(in_page_df, "InPage")
    write_as_csv(block_properties_df, "BlockHasProperty")


def save_graph_links(graph: Graph) -> None:
    """Store direct link info from graph in a CSV file."""
    links_df = polars.DataFrame(graph.links)
    write_as_csv(links_df, "Links")


def save_graph_page_props(graph: Graph) -> None:
    """Store page properties from graph in CSV files."""
    pages_with_properties = []

    for prop, pages_with_prop in graph.page_properties.items():
        # Tweaking nested strings until Kuzu issue #3461 is resolved.
        # - https://github.com/kuzudb/kuzu/issues/3461
        pages_with_properties += [
            {"from": page, "to": prop, "value": value.replace('"', "*")}
            for page, value in pages_with_prop.items()
        ]

    page_props_df = polars.DataFrame(pages_with_properties)
    write_as_csv(page_props_df, "PageHasProperty")


def save_graph_namespaces(graph: Graph) -> None:
    """Store page namespaces from graph in a CSV file."""
    namespaces = []

    for page in graph.pages.values():
        if page.namespace == NAMESPACE_SELF:
            continue

        info = {"from": page.name, "to": page.namespace}
        namespaces.append(info)

    namespaces_df = polars.DataFrame(namespaces)
    write_as_csv(namespaces_df, "InNamespace")


def save_graph_page_tags(graph: Graph) -> None:
    """Store page tags from graph in a CSV file."""
    page_tags = []

    for tag, pages_with_tags in graph.page_tags.items():
        for page in pages_with_tags:
            info = {"from": page, "to": tag}
            page_tags.append(info)

    page_tags_df = polars.DataFrame(page_tags)
    write_as_csv(page_tags_df, "PageIsTagged")


def save_graph_pages(graph: Graph) -> None:
    """Store page info from graph in a CSV file."""
    pages = [
        {
            "name": page.name,
            "is_placeholder": page.is_placeholder,
            "is_public": page.is_public,
        }
        for page in graph.pages.values()
    ]
    pages_df = polars.DataFrame(pages)
    write_as_csv(pages_df, "Page")


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

    save_graph_pages(graph)
    save_graph_namespaces(graph)
    save_graph_links(graph)
    save_graph_page_props(graph)
    save_graph_page_tags(graph)
    save_graph_blocks(graph)

    conn = create_db(DB_NAME, DB_SCHEMA_PATH)
    populate_database(conn)


if __name__ == "__main__":
    main()

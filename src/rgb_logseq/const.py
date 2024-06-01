"""Constant values relied on throughout the application."""

import logging

from rich.logging import RichHandler

MARK_BLOCK_OPENER = "-"
MARK_BLOCK_CONTINUATION = " "
MARK_BLOCK_INDENT = "\t"
MARK_CODE_FENCE = "```"
MARK_DIRECTIVE_OPENER = "#+BEGIN"
MARK_DIRECTIVE_CLOSER = "#+END"
MARK_DIRECTIVE_SPLIT = "_"
MARK_PROPERTY = ":: "

logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
logger = logging.getLogger("rgb-logseq")

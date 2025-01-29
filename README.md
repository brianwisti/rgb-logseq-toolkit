# Random Geekery Blog Logseq Toolkit

## Summary

Using assorted tools to untangle my [Logseq][logseq] pages and graphs.

[logseq]: https://logseq.com/

## Goals

- Unify my Logseq setup across macOS and Linux
- Process Logseq notes for analysis
- Clean up inconsistent formatting and properties
- Publish my Logseq notes to [My Public Brain][my-brain]
- Translate my Logseq notes to other PKM systems
- (eventually) get all the pieces behaving nicely on Windows

[my-brain]: https://randomgeekery.org

## Caveat

This very initial push is still hard-coded to my particular workflow, and I'm
writing this file when I should be finishing up moving prep. There are probably
hard-coded aspects for my workflow, so *look* at the code before you run
anything.

## Tools

Initial code sketches – or "prototypes" if your background isn't in art –
are in [Python][python]. If performance, portability, or my attention span
become an issue, I may port my sketches to [Go][go-lang] or [Rust][rust].

[just][just] runs the tasks.

Processing and analysis are needed at individual, object collection, and full
graph level. I use [Polars][polars] for processing at the collection level.
Graph processing is managed with the [Kùzu][kuzu] embedded graph database,
though I'm still evaluating that particular bit of tooling.

Kùzu's interactive explorer runs as a container, so you'll almost certainly
want to have [Docker][docker] working.

[python]: https://python.org
[go-lang]: https://go.dev/
[rust]: https://www.rust-lang.org/
[polars]: https://pola.rs/
[kuzu]: https://kuzudb.com/
[just]: https://just.systems/
[docker]: https://www.docker.com/
[uv]: https://github.com/astral-sh/uv

### Python specifics

I'm on 3.12 via a `.venv` managed by [uv][uv]. Tests are managed with
[`pytest`][pytest], while [Ruff][ruff] and [mypy][mypy] look for code quality
issues. [Rich][rich] is there to make my console pretty.

[pytest]: https://docs.pytest.org/
[ruff]: https://astral.sh/ruff
[mypy]: https://mypy-lang.org/
[rich]: https://rich.readthedocs.io

## Setup

These instrutions assume a uv-based workflow. If you're using another set of tools, you'll need to modify for your own workflow.

Create a virtual environment to hold project-specific dependencies.

```bash
uv venv
```

Sync your venv with project dependencies.

```bash
uv sync
```

### Activating the virtual environment

Adding because it's the sort of trivia I'm always forgetting. Check `.venv/Scripts` for the `activate.*` script appropriate to your platform. Here's my main ones:

Linux or other UNIX-like with GNU Bash:

```bash
source .venv/bin/activate
```

Nushell:

```nu
overlay use .venv/Scripts/activate.nu
```

### Application Environment

Specify the location of your graph in your shell environment or a `.env` file.

```sh
GRAPH_PATH = "~/my-logseq-brain"
```

#### `kuzu`

To use the `kuzu` REPL or interactive explorer, install that.

For those macOS and Linux folks using Homebrew:

```bash
brew install kuzu
```

To use Kùzu's interactive explorer, make sure Docker is set up and running on
your system. Details on that vary enough that I won't bother breaking it down
here.

## Actions

### Development

Write code. Run tests. Run linter and type checks.

```bash
just test check
```

### Build the database

You can do this with only the Python dependencies installed. You'll
have to do all the graph analysis via Python if you stop here though.

```bash
just db
```

This generates a fresh database in `graph_db/`, removing any data previously in
place.

### Look at the pretty

Make sure you have the `kuzu` executable and Docker installed on your system.

```bash
just explore
```

Remember you can combine tasks, so if you want to explore a guaranteed[^1] fresh
database:

```bash
just db explore
```

## License

Using the MIT License for this.

Copyright 2024-2025 Brian Wisti

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the “Software”), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

[^1]: this software comes with no guarantees, explicit or implied. Good luck!

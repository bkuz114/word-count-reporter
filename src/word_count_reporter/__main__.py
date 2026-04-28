#!/usr/bin/env python3
"""Module execution wrapper: `python -m word_count_reporter`

STOP: Are you trying to run this tool directly from source?

    If you have NOT installed via pip, use cli.py directly:
        $ python src/word_count_reporter/cli.py [arguments]

    This file (__main__.py) is ONLY for the `python -m` pattern.

QUICK REFERENCE: Which entry point should you use?

    | Invocation | When to use |
    |------------|-------------|
    | `word-count-reporter` | Daily use (after `pip install`) |
    | `python -m word_count_reporter` | After install, if console script not in PATH |
    | `python src/.../cli.py` | Development (no install) |

WHY THIS FILE EXISTS:

The `python -m` flag is a Python convention that runs a package as a script.
This wrapper allows that pattern. It simply imports `main()` from `cli.py`
and executes it.

For most users after `pip install`, the console script (`word-count-reporter`)
is the recommended entry point. This file exists for completeness and
environments where the console script is not available.

EXAMPLE:

    # After pip install (recommended)
    word-count-reporter input.txt

    # After pip install (alternative)
    python -m word_count_reporter input.txt

    # From source (no install)
    python src/word_count_reporter/cli.py input.txt
"""

from .cli import main

if __name__ == "__main__":
    main()

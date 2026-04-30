# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## UNRELEASED

### Changed
- Replaced bespoke inputfile parser with vendored JSON parser (`inputfile-parser`)
- Input file format is now JSON (see example_files/example_inputfile.json)
- Multiple files per chapter are now supported
- Backup filenames now derived from source file names (not chapter names)

### Removed
- Legacy `utils/inputfile.py` and its bespoke format
- `parse_input_file()` function
- `example_inputfile.txt` (legacy format)

### Added
- Vendored `inputfile.py` from inputfile-parser v1.0.0
- `example_inputfile.json` (JSON format example)
- `vendor/__init__.py` and `vendor/VENDORED.md`
- Support for per-file custom display names

## [1.0.0] - 2026-04-28

### Added
- First PyPI release
- `src/` layout with proper Python packaging (`pyproject.toml`)
- Console script: `word-count-reporter` (available after `pip install`)
- `--version` flag showing version number
- Module execution support: `python -m word_count_reporter`
- Comprehensive docstrings for all functions (Google style)
- Type hints throughout codebase
- Modernized code: pathlib, f-strings, PEP8 compliance
- Professional HTML report styling with external CSS/JS
- PHP web interface with secure upload handling
- MIT License
- `.gitignore` for Python, PHP, and temporary files

### Changed
- Path resolution: relative input/output paths resolve to current working directory (not script location)
- Report output directory: writes to `./reports/` in current working directory
- Moved templates to `src/word_count_reporter/templates/`
- Improved CLI help text with clearer descriptions

### Fixed
- ModuleNotFoundError when installing via pip (utils package now included)
- Missing DOCTYPE and charset in generated HTML reports
- XSS vulnerabilities in PHP web interface (added htmlspecialchars)
- Command injection in PHP upload handler (added escapeshellarg)

### Removed
- Hardcoded absolute `REPORT_DIR` path (now uses `Path.cwd()`)
- Legacy `-i/--input` flag (now positional `INPUTFILE`)

---

[0.1.0]: https://github.com/bkuz114/word_count_reporter/releases/tag/v0.1.0

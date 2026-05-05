# Word Count Reporter

[![PyPI version](https://badge.fury.io/py/word-count-reporter.svg)](https://pypi.org/project/word-count-reporter/)
[![Python versions](https://img.shields.io/pypi/pyversions/word-count-reporter.svg)](https://pypi.org/project/word-count-reporter/)

Generate offline HTML word count reports from collections of text (.txt), Microsoft Word (.docx), Rich Text Format (.rtf), and markdown (.md, .markdown) documents.

## Features

- Counts words in `.txt`, `.docx`, `.rtf`, `.md`, and `.markdown` files
- Generates a sortable HTML report with chapter-by-chapter word counts
- Optionally backs up source files as plain text alongside the report
- Self-contained HTML report (no external dependencies after generation)
- Web interface for file upload and report generation (PHP)

# Quickstart

```bash
pip install word-count-reporter
word-count-reporter INPUTFILE
```

The generated report will open automatically in your browser (prevent browser open with `--no-browser` flag). That's it.

## Installation

### Option 1: Pip install (recommended for most users)

```bash
pip install word-count-reporter
```

### Option 2: Run from source (development or custom builds)

```bash
git clone https://github.com/REPO/word-count-reporter
cd word-count-reporter
pip install -e .
```

#### From within virtual environment (recommended)

```bash
# Create virtual environment
virtualenv venv

# Activate on Windows (CMD)
venv\Scripts\activate

# Activate on Windows (Git Bash)
source venv/Scripts/activate

# Activate on macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Pip package

```bash
word-count-reporter INPUTFILE [options]
```

### Command Line Interface

```bash
python word_count_reporter.py INPUTFILE [options]
```

## Usage Options

Whether installed via pip or run from source, the same options apply:

| Invocation method | Command |
|-------------------|---------|
| Pip-installed | `word-count-reporter INPUTFILE [OPTIONS]` |
| From source | `python src/word_count_reporter/cli.py INPUTFILE [OPTIONS]` |

### Options

| Option | Description |
|--------|-------------|
| `INPUTFILE` | Input file describing the project title and chapter files |
| `-o OUTPUT`, `--output OUTPUT` | Output file path. If not supplied, auto-generated from title and timestamp. When used with `--backup`, this specifies a directory. |
| `-b`, `--backup` | Backup source files as text files in the report directory. `.docx` and `.rtf` files are converted to `.txt`; `.txt` files are copied as-is. |
| `-t`, `--no-timestamp` | Omit timestamp from auto-generated output filename. |
| `-u`, `--use-title` | Use project title in auto-generated output filename. |
| `--no-browser` | Prevents browser from automatically opening with the report upon completion. |
| `-F`, `--FORCE` | Overwrite output file if it already exists. |
| `--log-level {debug,info}` | Set logging verbosity (default: `info`). |
| `-h`, `--help` | Show help message and exit. |
| `--version` | Show version number and exit. |

## Input File Format

The input file is a JSON file that defines the project title and lists the documents to be processed.

### Example Input file

```json
{
  "title": "My Book",
  "root": "./documents",
  "chapters": [
    {
      "number": 1,
      "name": "Introduction",
      "files": ["intro.txt"]
    },
    {
      "files": ["chapter2.txt"]
    }
  ]
}
```

### Metadata

Optional key-value pairs that configure the report. Supported keys:

| Key | Description |
|-----|-------------|
| `title` | Project title displayed in the report header. |
| `root` | Base directory for relative file paths in the `[book]` section. **For web interface, this must be an absolute path.** |

### Chapters

The `chapters` array defines the structure of your document. Each chapter object supports the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | integer | No | Chapter number (auto-incremented if omitted) |
| `name` | string | No | Chapter title (defaults to `"Chapter X"` if omitted) |
| `files` | array | Yes | One or more source files for this chapter |

#### Multiple files per chapter

A chapter can span multiple files. Specify them as an array:

```json
{
  "name": "Introduction",
  "files": ["intro_part1.txt", "intro_part2.txt", "intro_part3.txt"]
}
```

In the generated report, all files will be listed under the same chapter row, each with a clickable link.

#### Custom file display names

For each file, you can optionally specify a custom display name that will appear in the report (appended to the chapter name). Use the object syntax:

```json
{
  "name": "Introduction",
  "files": [
    "intro_overview.txt",
    {"path": "legal_disclaimer.pdf", "name": "Disclaimer"},
    {"path": "appendix.pdf", "name": "Supplemental Reading"}
  ]
}
```

In the report, these will appear as:
- `Introduction`
- `Introduction: Disclaimer`
- `Introduction: Supplemental Reading`

The simple string form (`"intro_overview.txt"`) uses the filename as the display name.

#### Auto-numbering and default names

If you omit `number`, chapters are numbered sequentially starting from 1. If you omit `name`, the chapter is titled `"Chapter X"` (where X is the chapter number). A chapter with both omitted:

```json
{"files": ["chapter2.txt"]}
```

...will appear as `"Chapter 2"` in the report.

### Web Interface (PHP)

A minimal web interface is included for users who prefer a GUI. The interface allows uploading an input file and optionally backing up source files.

#### Requirements

- PHP 7.4 or higher
- Web server (Apache, Nginx, or PHP's built-in server)
- Python 3.6+ with dependencies installed
- Fileinfo PHP extension (recommended)

### Quick Start (Web UI)

From the `web_ui` directory, start a PHP web server:

```bash
cd web_ui
php -S localhost:8000
```

Then open `http://localhost:8000` in your browser.

### Important: Absolute Paths Required

When using the web interface, chapter files must use **absolute paths** in your input file, or you must set the `root` key to an absolute path.

Reason: Uploaded input files are moved to a temporary location on the server. The web server cannot access your local file system's original paths. To ensure chapter files are found, use one of the following approaches:

**Option 1: Absolute paths in chapter entries**

```
[book]
::C:/Users/YourName/Documents/chapter1.txt
::C:/Users/YourName/Documents/chapter2.docx
```

**Option 2: Absolute `root` path with relative chapter entries**

```
[keys]
root: C:/Users/YourName/Documents

[book]
::chapter1.txt
::chapter2.docx
```

#### PHP Configuration

If you encounter a `Call to undefined function finfo_open()` error, enable the Fileinfo extension:

**Windows (XAMPP/WAMP):**
1. Open `php.ini` (e.g., `C:\xampp\php\php.ini`)
2. Find `;extension=fileinfo` or `;extension=php_fileinfo.dll`
3. Remove the semicolon to uncomment
4. Restart your web server

**Linux/macOS:**
```bash
sudo apt-get install php-fileinfo   # Debian/Ubuntu
sudo yum install php-fileinfo        # RHEL/CentOS
sudo phpenmod fileinfo               # Enable the extension
sudo systemctl restart apache2       # Restart web server
```

## Examples

### Pip-installed CLI

```bash
# Basic usage
# Generates an HTML report with word counts for all files listed in `example_inputfile.txt`.
word-count-reporter example_inputfile.txt

# With custom output location
python word_count_reporter.py example_files/example_inputfile.txt -o my_report.html

# With backup
# Creates a directory containing both the HTML report and plain-text copies of all source files.
python word_count_reporter.py example_files/example_inputfile.txt --backup

# With backup and custom output
word-count-reporter example_inputfile.txt --backup -o my_report.html

# Overwrite existing report
word-count-reporter example_inputfile.txt -o my_report.html -F

# Use project title in filename
# Generates a file like `My_Project-word-count-report_2025_01_15-14_30_00.html`.
word-count-reporter example_inputfile.txt --use-title
```

### From source (no installation)

```bash
python src/word_count_reporter/cli.py example_inputfile.txt
python src/word_count_reporter/cli.py example_inputfile.txt --backup -o my_report.html
```

### Web interface

1. Start the PHP server: `cd web_ui && php -S localhost:8000`
2. Open `http://localhost:8000/index.html`
3. Upload your input file (with absolute paths)
4. Optionally check "Back up source files as text"
5. Click "Generate Report"

## Output

The script generates a self-contained HTML report containing:

- Project title and generation timestamp
- Sortable table with word counts per chapter
- Links to source files (original or backed-up versions)
- Total word count across all chapters

When using the command line, the report automatically opens in your default web browser after generation (unless `--no-browser` flag given). The web interface displays a link to the generated report.

## Troubleshooting

### File not found errors

**Command line:** Ensure file paths in the `[book]` section are correct. Use the `root` key to set a base directory for relative paths.

**Web interface:** Chapter files must use absolute paths, or `root` must be an absolute path. The web server cannot resolve relative paths from your local machine.

### Unsupported file type

Only `.txt`, `.docx`, `.rtf`, `.md`, and `.markdown` files are currently supported. Other file types will raise an error.

### Output file exists

Use `-F` or `--FORCE` to overwrite an existing output file.

### finfo_open() error in web interface

Enable the PHP Fileinfo extension (see PHP Configuration section above).

### Permission denied when writing reports

The script writes reports to `./reports/` (current working directory). Ensure you have write permissions in that location.

### Command not found (Windows)

Use `python` or `py` depending on your installation. You may need to use the full path to Python or add it to your PATH.

## License

MIT License

## Contributing

Issues and pull requests are welcome. Please ensure code passes existing tests and includes appropriate documentation updates.


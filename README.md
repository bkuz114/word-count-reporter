# Word Count Reporter

Generate an HTML word count report from a collection of text (.txt) and Microsoft Word (.docx) documents.

## Features

- Counts words in `.txt` and `.docx` files
- Generates a sortable HTML report with chapter-by-chapter word counts
- Optionally backs up source files as plain text alongside the report
- Self-contained HTML report (no external dependencies after generation)

## Installation

### Dependencies

```bash
pip install beautifulsoup4 python-docx
```

Or using the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Virtual environment (recommended)

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

```bash
python word_count_reporter.py INPUTFILE [options]
```

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `INPUTFILE` | Input file describing the project title and list of chapter files |

### Options

| Option | Description |
|--------|-------------|
| `-o OUTPUT`, `--output OUTPUT` | Output file path. If not supplied, auto-generated from title and timestamp in a `reports/` dir created within script dir. When used with `--backup`, this specifies a directory. |
| `-b`, `--backup` | Backup source files as text files in the report directory. `.docx` files are converted to `.txt`; `.txt` files are copied as-is. |
| `-t`, `--notimestamp` | Omit timestamp from auto-generated output filename. |
| `-u`, `--usetitle` | Use project title in auto-generated output filename. |
| `-F`, `--FORCE` | Overwrite output file if it already exists. |
| `--loglevel {debug,info}` | Set logging verbosity (default: `info`). |
| `-h`, `--help` | Show help message and exit. |

## Input File Format

The input file defines the project title and lists the documents to be processed. It consists of two sections: `[keys]` and `[book]`.

### Example Input File

```
[keys]
title: Example Project
root: ./documents

[book]
:Chapter One:introduction.docx
2:Background:background.docx
::section1.txt
::section2.txt
```

### Section: `[keys]`

Optional key-value pairs that configure the report. Supported keys:

| Key | Description |
|-----|-------------|
| `title` | Project title displayed in the report header. |
| `root` | Base directory for relative file paths in the `[book]` section. |

### Section: `[book]`

Lists the documents to process. Each line follows the format:

```
[chapter_number]:[chapter_name]:[filepath]
```

#### Field Rules

| Field | Description |
|-------|-------------|
| `chapter_number` | Optional. If omitted, numbering continues from previous chapter (starting at 1). |
| `chapter_name` | Optional. If omitted, defaults to the base filename of `filepath`. |
| `filepath` | Required. Path to a `.txt` or `.docx` file. Relative paths are resolved against the `root` key (if provided) or the input file's directory. |

#### Examples

| Line | Resulting Chapter # | Resulting Chapter Name | Source File |
|------|--------------------|------------------------|-------------|
| `::chapter1.txt` | 1 (auto) | `chapter1.txt` | `chapter1.txt` |
| `:Introduction:intro.docx` | 2 (auto) | `Introduction` | `intro.docx` |
| `5:Chapter Five:ch5.docx` | 5 | `Chapter Five` | `ch5.docx` |

## Examples

### Basic usage

```bash
python word_count_reporter.py example_inputfile.txt
```

This generates an HTML report with word counts for all files listed in `example_inputfile.txt`.

### With backup

```bash
python word_count_reporter.py example_inputfile.txt --backup
```

Creates a directory containing both the HTML report and plain-text copies of all source files.

### Custom output location

```bash
python word_count_reporter.py example_inputfile.txt -o my_report.html
```

### Overwrite existing report

```bash
python word_count_reporter.py example_inputfile.txt -o my_report.html -F
```

### Using project title in filename

```bash
python word_count_reporter.py example_inputfile.txt --usetitle
```

Generates a file like `My_Project-word-count-report_2025_01_15-14_30_00.html`.

## Output

The script generates a self-contained HTML report containing:

- Project title and generation timestamp
- Sortable table with word counts per chapter
- Links to source files (original or backed-up versions)
- Total word count across all chapters

The report automatically opens in your default web browser after generation.

## Troubleshooting

### File not found errors

Ensure file paths in the `[book]` section are correct. Use the `root` key in `[keys]` to set a base directory for relative paths.

### Unsupported file type

Only `.txt` and `.docx` files are supported. Other file types will raise an error.

### Output file exists

Use `-F` or `--FORCE` to overwrite an existing output file.

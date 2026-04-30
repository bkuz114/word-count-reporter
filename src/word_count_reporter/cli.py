#!/usr/bin/env python3
"""Word count reporter for text and DOCX documents.

This script reads an input file containing a project title and a list of
chapters with their corresponding file paths, counts the words in each
document (.txt or .docx), and generates an HTML report with a table of
word counts.

Usage:
    python word_count_reporter.py INPUT_FILE [OPTIONS]

Input file format:
    The input file must be parsable by the custom inputfile module.
    Expected structure: title line followed by chapter entries, each with
    a chapter name and file path.

Dependencies:
    - python-docx: for reading .docx files
    - beautifulsoup4: for HTML generation
    - inputfile (local module): for parsing the input file format
    - report_template.html: must exist in the working directory

Output:
    Generates an HTML report and opens it in the default web browser.
    Optionally backs up source files as .txt in a subdirectory.
"""

from datetime import datetime as dt
from docx import Document
from bs4 import BeautifulSoup
from typing import Any, Optional, Union
import webbrowser
import sys
import argparse
import shutil
import logging
from pathlib import Path

# Allow direct execution from source during development (e.g., `python cli.py`)
# by adding the `src/` directory to Python's import path. This block only runs
# when the script is executed directly, not when imported as a module or run
# from a pip installation.
if __name__ == "__main__":
    src_dir = Path(__file__).resolve().parent.parent  # resolve() to handle symlinks
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

# Now absolute imports work even when running directly
from word_count_reporter.utils import inputfile
from word_count_reporter import __version__

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_DIR = Path.cwd() / "reports"
TEMPLATES_DIR = SCRIPT_DIR / "templates"
# dir where js and css to embed live
ASSETS_SRC = TEMPLATES_DIR / "assets"

ENC = "utf-8"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a word count report from text and DOCX documents.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input",
        metavar="INPUTFILE",
        type=Path,
        help="Input file describing project title and chapter file paths",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="""Output file. If not supplied,
                        will be based on title and timestamp""",
        required=False,
    )
    parser.add_argument(
        "-b",
        "--backup",
        required=False,
        action="store_true",
        help="Backup input files as text files in the same "
        "directory holding the report. Notes: "
        "(1) if any of the files are .docx files, will "
        "convert them to text files; .txt files will be "
        "backed up as is; other file type not supported."
        " (2) if --backup and --output both given, "
        "then --output should be the directory for both "
        "the report and the backed up "
        "files, NOT the path to the report itself.",
    )
    parser.add_argument(
        "-t",
        "--no-timestamp",
        required=False,
        action="store_true",
        help="Don't timestamp output file",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser once report is generated.",
    )
    parser.add_argument(
        "-u",
        "--use-title",
        required=False,
        action="store_true",
        help="When --output not given, use the project's "
        "title in filename generated for the report.",
    )
    parser.add_argument(
        "--log-level", default="info", choices=["debug", "info"], help="Log level."
    )
    parser.add_argument(
        "-F",
        "--FORCE",
        required=False,
        action="store_true",
        default=False,
        help="Overwrite output file if exists",
    )
    parser.add_argument("--version", action="version", version=f"{__version__}")
    return parser.parse_args()


# -----------------------------------------------------------------------------
# MAIN SETUP
# -----------------------------------------------------------------------------


def enable_logging(log_level_arg: str) -> None:
    """Configure the root logger with the given log level.

    Sets the logger's severity threshold and attaches a console handler
    for output. Only intended to be called once at startup.

    Args:
        log_level_arg: Case-insensitive log level string. Accepted values are
            "debug" and "info". Any unrecognized value defaults to DEBUG.
    """
    loglevel = logging.DEBUG
    if log_level_arg:
        match log_level_arg:
            case "debug":
                loglevel = logging.DEBUG
            case "info":
                loglevel = logging.INFO
    logger.setLevel(loglevel)
    console = logging.StreamHandler()
    # console.setFormatter(logging.Formatter('%(name)-12s: %(message)s'))
    logger.addHandler(console)


def determine_output_paths(
    output_arg: Path | None,
    title: str,
    use_title: bool,
    no_timestamp: bool,
    backup: bool,
    default_report_dir: Path,
) -> tuple[Path, Path | None]:
    """
    Determines path to report file and optional backup dir
    based on user-provided flags.

    Args:
        output_arg: Output directory from --output
        title: Project title (used for constructing dir, filename when use_title True).
        use_title: (boolean) Whether --use-title flag set. When True, a per-run
            subdir of project title created. Also prependeds to report filename.
            *NOTE*: whitespace converted to _ to avoid scripting issues
        no_timestamp: (boolean) Whether --no-timestamp flag set. When True,
            pre-run timestamps are NOT appeanded to directory or filenames.
            WARNING: When combined with backup, per-run backup dir may collide with
            repeated runs of same project (i.e. reports/myproject1/ will have a
            "backup_run/" dir each run of the project)
        backup: (boolean) Whether --backup was given. When True, output is
            placed in a per-run subdirectory.
        default_report_dir: Default output directory when output_arg not provided.

    Returns: tuple (report_file, backup_dir) where:
        - report_file: full path for the HTML report
        - backup_dir: full path to backup subdirectory (or None if backup == False)

    Examples:
        # No flags (flat files in default output dir)
        /reports/report_20260429_143052.html

        # --use-title (dedicated project dir + title on filename)
        /reports/Project_1/Project_1-report_20260429_143052.html

        # --no-timestamp
        /reports/report.html
        *WARNING*: collisions on repeated runs

        # --use-title --no-timestamp
        /reports/Project_1/Project_1-report.html
        *WARNING*: collisions on repeated runs of same project

        # --backup
        /reports/backup_run-20260429_143052/
            report_20260429_143052.html
            backups/* <-- input files backed up here

        # --backup --use-title
        /reports/Project_1/backup_run-Project_1-20260429_143052/
            Project_1-report_20260429_143052.html
            backups/ <-- input files backed up here

        # --backup --no-timestamp
        /reports/backup_run/
            report.html
            backups/ <-- input files backed up here
        *WARNING*: collisions on repeated runs

        # --backup --use-title --no-timestamp
        /reports/Project_1/backup_run-Project_1/
            Project_1-report.html
            backups/ <-- input files backed up here
        *WARNING*: collisions on repeated runs of same project

        # --output /custom --backup --use-title
        /custom/Project_1/backup_run-20260429_143052/
            Project_1-report_20260429_143052.html
            backups/
    """
    ts = timestamp() if not no_timestamp else None
    # resolve custom output relative cwd
    if output_arg:
        output_arg = output_arg.resolve()
    # ensure title supplied if want to --use-title
    if use_title and not title:
        raise ValueError("No title when specifying --use-title")
    # convert whitespace to _ in title
    title = title.replace(" ", "_")

    # I: Base output directory. 3 options:
    output_dir = output_arg or default_report_dir
    if use_title:
        output_dir = output_dir / title

    # II: Output dir when backups=True:
    # When backing up, isolate this run in its own subdirectory so report
    # and backed up files will be contained together, (rather than spread
    # out in a single dir), and to prevent collisions with previous runs . e.g.
    #
    # reports/project1/
    # - report_4_29_1.html
    # - report_4_29_2.html <-- which report belongs to backup/ folder?
    # - backups/ <-- will be overwritten on subsequent run; instead want dedicated dir
    if backup:
        dir_name = f"backup_run-{ts}" if ts else "backup_run"
        # report + dedicated backup dir will live here
        output_dir = output_dir / dir_name

    # III: Report filename: optionally prefixed with title and suffixed with timestamp
    report_name = "report"
    if use_title:
        report_name = f"{title}-{report_name}"
    if ts:
        report_name += f"_{ts}"

    # IV: Final path to report and backup dir
    report_file = output_dir / f"{report_name}.html"
    backup_dir = output_dir / "backups" if backup else None

    return report_file, backup_dir


def parse_input_file(filepath: Path) -> tuple[str, list[list[Any]]]:
    """Parse the input file and extract title and chapter file paths.

    Args:
        filepath (Path): Path to the input file.

    Returns:
        tuple: (title, my_data) where:
            - title (str): Project title from input file.
            - my_data (list): List of [chapter_name (str), file_path (Path)] pairs.
    """
    if not filepath.exists():
        raise Exception(f"Input file {str(filepath)} does not exist!")

    title, file_data, inputfile_had_parts = inputfile.parse_data_file(str(filepath))
    my_data = []
    for data in file_data:
        filename = data[1]  # chapter name
        filepath = Path(data[2])  # filepath to chapter
        if not filename:  # if no chapter name, make it the name of the file
            filename = filepath.name
        my_data.append([filename, filepath])
    return title, my_data


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------


def timestamp() -> str:
    """Return a timestamp string safe for use in filenames.

    Returns:
        str: Current timestamp in format YYYY_MM_DD-HH_MM_SS.
    """
    # format the datetime without any spaces
    fmt = "%Y_%m_%d-%H_%M_%S"
    ct = dt.now().strftime(fmt)
    return str(ct)


def date_string() -> str:
    """human readable/useful date string"""
    date = dt.now()
    formatted_date = date.strftime("%B %d, %Y")

    time = dt.now()
    formatted_time = time.strftime("%I:%M:%S %p")

    return f"{formatted_date}, {formatted_time}"


def file_url(filepath: Path) -> str:
    """Convert a local file path to a file:// URL for HTML links.

    Args:
        filepath (Path): Local file path (backslashes allowed).

    Returns:
        str: URL in format file:///C:/path/to/file.
    """
    filestr = str(filepath).replace("\\", "/")
    filestr = "file:///" + filestr
    return filestr


def number(numstr: Union[int, str]) -> str:
    """Format a number with thousand separators.

    Args:
        numstr (int or str): Number to format.

    Returns:
        str: Number with commas as thousand separators.
    """
    return f"{numstr:,}"


# -----------------------------------------------------------------------------
# FILE I/O
# -----------------------------------------------------------------------------


def file_contents(filepath: Path) -> str:
    """Read and return the entire contents of a text file.

    Args:
        filepath (Path): Path to the file to read.

    Returns:
        str: File contents.

    Raises:
        Exception: If the file does not exist.
    """
    if not filepath.exists():
        raise Exception(f"{str(filepath)} doesn't exist")
    file = open(filepath, "r", encoding=ENC)
    file_str = file.read()
    file.close()
    return file_str


def write_file(filepath: Path, data: str, force: bool) -> None:
    """Write data to a file, creating directories as needed.

    Args:
        filepath (Path): Absolute path to the output file.
        data (str): Content to write.
        force (bool): If True, overwrite existing file. If False, require
                      that the file does not already exist.

    Raises:
        Exception: If filepath is not absolute.
        Exception: If file exists and force is False.
    """
    if not filepath.is_absolute():
        raise Exception(f"Output file {str(filepath)} is not absolute!")
    if filepath.exists() and not force:
        raise Exception(
            f"Output file {str(filepath)} exists! " "Use --FORCE / -F" " to overwrite"
        )
    # create dirs in path if they don't exist
    basedir = filepath.parent
    basedir.mkdir(parents=True, exist_ok=True)

    mode = "w" if force else "x"
    with open(filepath, mode, encoding=ENC) as wr:
        wr.write(data)


def word_count_docx(filepath: Path) -> int:
    """Count words in a .docx file.

    Args:
        filepath (Path): Path to the .docx file.

    Returns:
        int: Number of words (split on whitespace per paragraph).
    """
    document = Document(str(filepath))
    num_words = 0
    for paragraph in document.paragraphs:
        words = paragraph.text.split()
        num_words += len(words)
    return num_words


def word_count_txt(filepath: Path) -> int:
    """Count words in a .txt file.

    Args:
        filepath (Path): Path to the .txt file.

    Returns:
        int: Number of words (split on whitespace per line).
    """
    num_words = 0
    with open(filepath, "r", encoding=ENC) as f:
        for line in f:
            words = line.split()
            num_words += len(words)
    return num_words


def file_word_count(filepath: Path) -> int:
    """Dispatch word counting based on file extension.

    Args:
        filepath (Path): Path to the file (.txt or .docx).

    Returns:
        int: Word count.

    Raises:
        Exception: If file does not exist or extension is not supported.
    """
    if not filepath.exists():
        raise Exception(f"File {str(filepath)} does not exist!")

    extension = filepath.suffix
    if extension == ".txt":
        return word_count_txt(filepath)
    if extension == ".docx":
        return word_count_docx(filepath)
    else:
        raise Exception(
            f"invalid filetype {extension}. "
            "Only .txt and .docx "
            "currently supported"
        )


def docx_to_txt(srcpath: Path, destpath: Path) -> None:
    """Convert a .docx file to a plain text file.

    Args:
        srcpath (Path): Path to the source .docx file.
        destpath (Path): Path for the output .txt file.

    Raises:
        Exception: If srcpath does not exist or destpath already exists.
    """
    if not srcpath.exists():
        raise Exception(
            f"Trying to convert a docx to txt, but the docx file doesn't exist: {str(srcpath)}"
        )
    if destpath.exists():
        raise Exception(
            f"Trying to convert a docx to a text file, "
            f"but proposed destination path already exists.\n\n"
            f"srcfile: {str(srcpath)}\ndest path: {str(destpath)}"
        )

    # need to create parent dir of file writing to or python will error
    destpath.parent.mkdir(parents=True, exist_ok=True)
    with open(destpath, "w", encoding=ENC) as destfile:
        document = Document(str(srcpath))
        for paragraph in document.paragraphs:
            destfile.write(paragraph.text + "\n")


# -----------------------------------------------------------------------------
# HTML CREATION
# -----------------------------------------------------------------------------


def total_row(total: int) -> BeautifulSoup:
    """Create an HTML table row for the total word count.

    Args:
        total (int): Total word count across all chapters.

    Returns:
        BeautifulSoup: HTML element representing the total row.
    """
    return BeautifulSoup(
        f"""
        <tr id="total">
            <td colspan="3">Total</td>
            <td>{number(total)}</td>
        </tr>
        """,
        "html.parser",
    )


def word_count_row(file_info: list[Any], row_num: int) -> BeautifulSoup:
    """Create an HTML table row for a single chapter's word count.

    Args:
        file_info (list): [chapter_name (str), file_path (Path), word_count (int)].
        row_num (int): Row number (1-indexed) for display.

    Returns:
        BeautifulSoup: HTML element representing the table row.
    """
    chapter_name = file_info[0]
    chapter_path = file_url(file_info[1])
    word_count = number(file_info[2])

    return BeautifulSoup(
        f"""
        <tr>
            <td>{row_num}</td>
            <td>{chapter_name}</td>
            <td><a href="{chapter_path}" target=_blank>file</a></td>
            <td>{word_count} words</td>
        </tr>
        """,
        "html.parser",
    )


def generate_report(
    title: str, word_count_info: list[Any], outfile: Path, force: bool
) -> Path:
    """Generate an HTML report from word count data.

    Args:
        title (str): Project title.
        word_count_info (list): List of [chapter_name (str), file_path (Path), word_count (int)].
        outfile (Path): Output HTML file path.
        force (bool): Overwrite output file if exists.

    Returns:
        Path: Path to the generated report file.
    """
    date = date_string()

    contents = file_contents(TEMPLATES_DIR / "report_template.html")
    # css and js to embed
    css_contents = file_contents(ASSETS_SRC / "style.css")
    js_contents = file_contents(ASSETS_SRC / "scripts.js")

    contents = contents.replace("%title%", title)
    contents = contents.replace("%date%", date)
    # embed css and js for portability
    contents = contents.replace("%css%", css_contents)
    contents = contents.replace("%script%", js_contents)

    soup = BeautifulSoup(contents.encode(ENC), "html.parser")

    # Get <tbody> in word-count-table
    table = soup.find(attrs={"id": "word-count-table"})
    if not table:
        raise RuntimeError("Could not find table with id='word-count-table'")
    tbody = table.find("tbody")
    if not tbody:
        raise RuntimeError("Table missing required <tbody> element")

    # append rows directly to <tbody>
    total_words = 0
    for idx, count_info in enumerate(word_count_info):
        tbody.append(word_count_row(count_info, idx + 1))
        total_words += count_info[2]
    tbody.append(total_row(total_words))

    pretty_soup = soup.prettify(formatter="html")
    write_file(outfile, pretty_soup, force)
    return outfile


def make_report(
    title: str, file_info_list: list[list[Any]], outfile: Path, force: bool
) -> Path:
    """Augment file info with word counts and generate the report.

    Args:
        title (str): Project title.
        file_info_list (list): List of [chapter_name (str), file_path (Path)] pairs.
        outfile (Path): Output HTML file path.
        force (bool): Overwrite output file if exists.

    Returns:
        Path: Path to the generated report file (returned by generate_report).
    """
    for file_info in file_info_list:
        filepath = Path(file_info[1])
        file_info.append(file_word_count(filepath))
    return generate_report(title, file_info_list, outfile, force)


# -----------------------------------------------------------------------------
# BACKUP LOGIC
# -----------------------------------------------------------------------------


def backup_file(chapter_filepath: Path, chapter_name: str, backup_dir: Path) -> Path:
    """Back up a single file, converting .docx to .txt if needed.

    Args:
        chapter_filepath (Path): Path to the source file.
        chapter_name (str): Name of the chapter (used for naming .txt output
                            when converting from .docx).
        backup_dir (Path): Destination directory for the backup.

    Returns:
        Path: Path to the backed-up file.

    Raises:
        Exception: If file extension is not .txt or .docx.
    """
    logger.debug(
        f"Back up:\n\t* chapter: {chapter_name}\n\t* src    : {str(chapter_filepath)}\n\t* dest   : {str(backup_dir)}"
    )
    extension = chapter_filepath.suffix
    dest_filepath = None  # will be a Path object
    if extension == ".docx":
        filename_no_ext = Path(
            chapter_name
        ).stem  # explore: isnt' chapter_name just a simple string (not a path)?
        dest_filepath = backup_dir / Path(filename_no_ext + ".txt")
        docx_to_txt(chapter_filepath, dest_filepath)
    elif extension == ".txt":
        filename = chapter_filepath.name
        dest_filepath = backup_dir / filename
        shutil.copyfile(str(chapter_filepath), str(dest_filepath))
    else:
        raise Exception("file to backup isn't .docx or .txt")
    logger.debug(f"\tFile backed up to: {str(dest_filepath)}")
    return dest_filepath


def backup(files_info: list[list[Any]], backup_dir: Path) -> list[Path]:
    """Back up all source files to a subdirectory.

    Args:
        files_info (list): List of [chapter_name (str), file_path (Path)] pairs.
        backup_dir (Path): Directory to back files up to.

    Returns:
        list[Path]: Paths to the backed-up files, in the same order as files_info.
    """
    destfiles = []
    for file_info in files_info:
        # 'backup' the file and add filepath of
        # backed up file to destfiles
        destfiles.append(backup_file(Path(file_info[1]), file_info[0], backup_dir))
    return destfiles


def setup_backup(input_data: list[list[str]], backup_dir: Path) -> list[list[str]]:
    """Back up input files and return input data referencing the copies.

    Copies each source file into backup_dir, then replaces the
    original file paths in input_data with the paths to the
    backed-up copies. This ensures the report is generated from the
    isolated backup files rather than the original sources.

    Args:
        input_data: List of chapters, where each entry is
            [chapter_name, source_filepath]
        backup_dir: Directory to place the backed-up files.

    Returns:
        A new list with the same chapter names and the paths to the
        backed-up file copies.

    Raises:
        RuntimeError: If backup_dir is None or not absolute.
    """
    if not backup_dir:
        raise RuntimeError("Bug: --backup specified, but backup_dir not determined")
    if not backup_dir.is_absolute():
        raise RuntimeError(f"Backup dir not absolute: {backup_dir}")

    # Copy all source files into the backup directory
    backup_files = backup(input_data, backup_dir)
    new_idata = []

    # Replace source paths with backup paths, preserving chapter names
    list_print = "\n".join(map(str, input_data))  # to pretty print list data
    logger.debug(f"original input data:")
    logger.debug(list_print)
    for original, backed_up in zip(input_data, backup_files):
        new_idata.append([original[0], backed_up])
    input_data = new_idata
    list_print = "\n".join(map(str, input_data))
    logger.debug(f"new input data:")
    logger.debug(list_print)

    return input_data


# -----------------------------------------------------------------------------
# MAIN ORCHESTRATION
# -----------------------------------------------------------------------------


def main() -> None:
    """Main entry point for the word-count-reporter CLI.

    Parses command-line arguments using argparse, which automatically
    reads from sys.argv. This function is called by:

    - The console script after pip install: word-count-reporter
    - Direct execution: python src/word_count_reporter/cli.py
    - Module execution: python -m word_count_reporter

    Returns:
        None
    """
    # handle CLI
    args = parse_args()

    # set up logger
    enable_logging(args.log_level)

    # parse input file
    input_file = args.input.resolve()  # resolve rel cwd
    # input_data is list of lists.
    # inner lists correspond to chapters: [name, path to file]
    title, input_data = parse_input_file(input_file)

    # determine paths for HTML report + backup dir
    output_dir = args.output.resolve() if args.output else None  # resolve rel cwd
    report_file, backup_dir = determine_output_paths(
        output_dir, title, args.use_title, args.no_timestamp, args.backup, REPORT_DIR
    )

    # backup input files
    if args.backup:
        # setup_backup returns version of input_data pointing to backed up
        # files, so can read from up files during report generation
        input_data = setup_backup(input_data, backup_dir)

    # create the HTML report
    report = str(make_report(title, input_data, report_file, args.FORCE))

    # print filepath to created report
    logger.info(report)

    # optionally open in browser
    if not args.no_browser:
        webbrowser.open(report)


if __name__ == "__main__":
    main()

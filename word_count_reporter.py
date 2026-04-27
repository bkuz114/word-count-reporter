from datetime import datetime as dt
from docx import Document
from bs4 import BeautifulSoup
import webbrowser
import sys
import os
import argparse
import inputfile
import shutil
import logging

logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPORT_DIR = (
    "C:\\Users\\Boris\\Documents\\programming\\git repos\\word-count-reporter\\reports"
)
ENC = "utf-8"


def main(args):

    parser = argparse.ArgumentParser(
        description="Create a word count report",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-i", "--input", required=True, help="Input file")
    parser.add_argument(
        "-o",
        "--output",
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
        "--notimestamp",
        required=False,
        action="store_true",
        help="Don't timestamp output file",
    )
    parser.add_argument(
        "-u",
        "--usetitle",
        required=False,
        action="store_true",
        help="When --output not given, use the project's "
        "title in filename generated for the report.",
    )
    parser.add_argument(
        "--loglevel", default="info", choices=["debug", "info"], help="Log level."
    )
    parser.add_argument(
        "-F",
        "--FORCE",
        required=False,
        action="store_true",
        default=False,
        help="Overwrite output file if exists",
    )
    args = parser.parse_args(args)

    # a logger for my debugging purposes
    loglevel = logging.DEBUG
    if args.loglevel:
        match args.loglevel:
            case "debug":
                loglevel = logging.DEBUG
            case "info":
                loglevel = logging.INFO
    logger.setLevel(loglevel)
    console = logging.StreamHandler()
    # console.setFormatter(logging.Formatter('%(name)-12s: %(message)s'))
    logger.addHandler(console)

    ifile = args.input
    if not os.path.exists(ifile):
        raise Exception("Input file {} does not exist!".format(ifile))
    if not os.path.isabs(ifile):
        ifile = os.path.abspath(os.path.join(SCRIPT_DIR, ifile))

    # parse the input file
    # note: input_data is array of arrays.
    # each inner array corresponds to a chapter.
    # each inner array is [chap name, path to file]
    title, input_data = parse_input_file(ifile)

    # generic output file and possibly folder
    # (if --backup, will encorporate a folder)

    generic_filename = "word-count-report"
    generic_folder = "word_count_w_backup"
    ts = timestamp()
    if args.usetitle:
        safe_title = title.replace(" ", "_")
        generic_filename = safe_title + "-" + generic_filename
        generic_folder = safe_title + "-" + generic_folder
    if not args.notimestamp:
        generic_filename += "_" + ts
        generic_folder += "_" + ts
    generic_filename += ".html"

    # determine report file path, and backup dir if needed

    report_dir = None  # dir to hold the report (and backups)
    report_filename = None  # name of the report

    if args.output:  # --output arg given
        root, ext = os.path.splitext(args.output)
        if args.backup:  # --backup given: --output should be a folder
            logger.debug("op #1: (--output, --backup)")
            if ext:
                raise Exception(
                    "\n--output and --backup given, but "
                    " --output appears to be a file (it has "
                    "an extension). If you're giving --backup "
                    "and --output, then --output should specify "
                    "a FOLDER, which will hold both the report "
                    "file as well as the backed up files :)"
                )
            report_dir = args.output
            report_filename = generic_filename
        else:  # --backup not given; --output should be a file (the report)
            logger.debug("op #2: (--output, no --backup)")
            if not ext:
                raise Exception("\n\n--output does not appear to be a file")
            report_dir = os.path.dirname(args.output)
            report_filename = os.path.basename(args.output)
    else:  # --output arg not given - use default
        report_dir = os.path.join(REPORT_DIR, title)
        report_filename = generic_filename
        if (
            args.backup
        ):  # if --backup, default report dir should be an extra FOLDER: it will hold backup + report
            logger.debug("op #3: (no --output, --backup)")
            report_dir = os.path.join(report_dir, generic_folder)

    # final path to the report
    report_file = os.path.join(report_dir, report_filename)
    if not os.path.isabs(report_file):
        report_dir = os.path.join(SCRIPT_DIR, report_file)

    logger.debug("report dir     : " + report_dir)
    logger.debug("report filename: " + report_filename)
    logger.debug("Report file    : " + report_file)

    # if the report dir doesnt exist, create it
    os.makedirs(report_dir, exist_ok=True)

    # 2:40 pm 10/10/24
    # 2:48

    logger.debug("original input data:")
    logger.debug(input_data)

    if args.backup:
        backup_files = backup(input_data, report_dir)
        new_idata = []
        logger.debug("loop through and back up files")
        # zip allows you to loop through 2 lists at once
        for original, backed_up in zip(input_data, backup_files):
            new_idata.append([original[0], backed_up])
        input_data = new_idata

    logger.debug("new input data:")
    logger.debug(input_data)

    report = make_report(title, input_data, report_file, args.FORCE)

    logger.info(report)
    webbrowser.open(report)


"""
returns 2 items:

    title
        the title of the project
    my_data
        array of arrays.
        one inner array for each chapter.
        each inner array is:
            [chapter name, filepath to chapter]
"""


def parse_input_file(filepath):
    title, file_data, inputfile_had_parts = inputfile.parse_data_file(filepath)
    my_data = []
    for data in file_data:
        filename = data[1]  # chapter name
        filepath = data[2]  # filepath to chapter
        if not filename:  # if no chapter name, make it the name of the file
            filename = os.path.basename(filepath)
        my_data.append([filename, filepath])
    return title, my_data


def make_report(title, file_info_list, outfile, force):
    for file_info in file_info_list:
        file_info.append(file_word_count(file_info[1]))
    return generate_report(title, file_info_list, outfile, force)


""" date string with no spaces for timestamping files """


def timestamp():
    # format the datetime without any spaces
    fmt = "%Y_%m_%d-%H_%M_%S"
    ct = dt.now().strftime(fmt)
    return str(ct)


""" human readable/useful date string"""


def date_string():

    date = dt.now()
    formatted_date = date.strftime("%B %d, %Y")

    time = dt.now()
    formatted_time = time.strftime("%I:%M:%S %p")

    return formatted_date + ", " + formatted_time


def file_contents(filepath):
    if not os.path.exists(filepath):
        raise Exception("{} doesn't exist".format(filepath))
    file = open(filepath, "r", encoding=ENC)
    file_str = file.read()
    file.close()
    return file_str


def write_file(filepath, data, force):
    if not os.path.isabs(filepath):
        raise Exception("Output file {} is not absolute!".format(filepath))
    if os.path.exists(filepath) and not force:
        raise Exception(
            "Output file {} exists! "
            "Use --FORCE / -F"
            " to overwrite".format(filepath)
        )
    # create dirs in path if they don't exist
    basedir = os.path.dirname(filepath)
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    if force:
        wr = open(filepath, "w", encoding=ENC)
    else:
        wr = open(filepath, "x", encoding=ENC)
    wr.write(data)
    wr.close()


def generate_report(title, word_count_info, outfile, force):

    date = date_string()

    contents = file_contents("report_template.html")

    contents = contents.replace("%title%", title)
    contents = contents.replace("%date%", date)

    soup = BeautifulSoup(contents.encode(ENC), "html.parser")

    # table = soup.find("table", {"id":"table"})
    table = soup.find(attrs={"id": "word-count-table"})

    total_words = 0
    for idx, count_info in enumerate(word_count_info):
        table.append(word_count_row(count_info, idx + 1))
        total_words += count_info[2]
    table.append(total_row(total_words))

    pretty_soup = soup.prettify(formatter="html")
    write_file(outfile, pretty_soup, force)
    return outfile


"""
takes a filepath on the filesystem
and returns a string that will open
it in the browser. i.e.
file:///C:/Users/Boris/file.txt
"""


def file_url(filepath):
    filestr = filepath.replace("\\", "/")
    filestr = "file:///" + filestr
    return filestr


def number(numstr):
    return f"{numstr:,}"


def word_count_row(file_info, row_num):

    return BeautifulSoup(
        """<tr>
                         <td>{}</td>
                         <td>{}</td>
                         <td><a href="{}" target=_blank>file</a></td>
                         <td>{} words</td>
                         </tr>""".format(
            row_num, file_info[0], file_url(file_info[1]), number(file_info[2])
        ),
        "html.parser",
    )


def total_row(total):
    return BeautifulSoup(
        """<tr id="total">
                         <td colspan="3">Total</td>
                         <td>{}</td>
                         </tr>""".format(number(total)),
        "html.parser",
    )


def word_count_docx(filepath):
    document = Document(filepath)
    num_words = 0
    for paragraph in document.paragraphs:
        words = paragraph.text.split()
        num_words += len(words)
    return num_words


def word_count_txt(filepath):
    num_words = 0
    with open(filepath, "r", encoding=ENC) as f:
        for line in f:
            words = line.split()
            num_words += len(words)
    return num_words


def file_word_count(filepath):

    if not os.path.exists(filepath):
        raise Exception("File {} does not exist!".format(filepath))

    extension = os.path.splitext(filepath)[1]
    if extension == ".txt":
        return word_count_txt(filepath)
    if extension == ".docx":
        return word_count_docx(filepath)
    else:
        raise Exception(
            "invalid filetype {}. "
            "Only .txt and .docx "
            "currently supported".format(extension)
        )


"""
backs up all the files in files_info,
and returns a list of filepaths to
those backed up files, in same order.
(Note: for each file to back up, if
the file is .txt, it copies it directly
to report_dir; if it's .docx, it converts
it to .txt and copies that to report_dir)
"""


def backup(files_info, report_dir):
    destfiles = []
    backup_dir = os.path.join(report_dir, "files")
    for file_info in files_info:
        # 'backup' the file and add filepath of
        # backed up file to destfiles
        destfiles.append(backup_file(file_info[1], file_info[0], backup_dir))
    return destfiles


""" backup a file and return path to that backed up file """


def backup_file(chapter_filepath, chapter_name, backup_dir):
    logger.debug(
        "\n\n*chapter name: {}\n* srcfile: {}\n* dest dir: {}".format(
            chapter_name, chapter_filepath, backup_dir
        )
    )
    extension = os.path.splitext(chapter_filepath)[1]
    dest_filepath = None
    if extension == ".docx":
        filename_no_ext = os.path.splitext(chapter_name)[0]
        dest_filepath = os.path.join(backup_dir, filename_no_ext + ".txt")
        docx_to_txt(chapter_filepath, dest_filepath)
    elif extension == ".txt":
        filename = os.path.basename(chapter_filepath)
        dest_filepath = os.path.join(backup_dir, filename)
        shutil.copyfile(chapter_filepath, dest_filepath)
    else:
        raise Exception("file to backup isn't .docx or .txt")
    logger.debug("\tFile backed up to: " + dest_filepath)
    return dest_filepath


""" convert a .docx file to a .txt file """


def docx_to_txt(srcpath, destpath):
    if not os.path.exists(srcpath):
        raise Exception(
            "Trying to convert a docx to txt, but the docx "
            " file doesn't exist: {}".format(srcpath)
        )
    if os.path.exists(destpath):
        raise Exception(
            "Trying to convert a docx to a text file, "
            "but proposed destination path already "
            "exists.\n\nsrcfile:{}\ndest path:{}".format(srcpath, destpath)
        )

    # need to create parent dir of file writing to or python will error
    os.makedirs(os.path.dirname(destpath), exist_ok=True)
    with open(destpath, "w", encoding=ENC) as destfile:
        document = Document(srcpath)
        for paragraph in document.paragraphs:
            destfile.write(paragraph.text + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])

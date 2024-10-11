from datetime import datetime as dt
from docx import Document
import webbrowser
import sys
import os
import argparse
import inputfile
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPORT_DIR = "C:\\Users\\Boris\\Documents\\programming\\git repos\\word-count-reporter\\reports"
ENC = 'utf-8'


def main(args):

    parser = argparse.ArgumentParser(
        description='Create a word count report',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', required=True,
                        help="Input file")
    parser.add_argument('-o', '--output',
                        help="""Output file. If not supplied,
                        will be based on title and timestamp""",
                        required=False)
    parser.add_argument('-t', '--notimestamp', required=False,
                        action="store_true",
                        help="Don't timestamp output file")
    parser.add_argument('-F', '--FORCE', required=False,
                        action="store_true",
                        default=False,
                        help='Overwrite output file if exists')
    parser.add_argument('--includepaths', required=False,
                        action="store_true",
                        default=False,
                        help='Include filepaths in the report.')
    args = parser.parse_args(args)

    ifile = args.input
    if not os.path.exists(ifile):
        raise Exception("Input file {} does not exist!"
                        .format(ifile))
    if not os.path.isabs(ifile):
        ifile = os.path.abspath(os.path.join(SCRIPT_DIR, ifile))

    # parse the input file
    title, input_data = parse_input_file(ifile)

    # output
    output = args.output
    if not output:
        report_basedir = os.path.join(REPORT_DIR, title)
        filename = title.replace(" ", "_") + "-word-count-report"
        if not args.notimestamp:
            ts = timestamp()
            filename += "_" + ts
        filename += ".html"
        output = os.path.join(report_basedir, filename)
    if not os.path.isabs(output):
        output = os.path.abspath(os.path.join(SCRIPT_DIR, args.output))

    # 2:40 pm 10/10/24
    # 2:48

    report = make_report(title, input_data, output, args.includepaths,
                         args.FORCE)
    print("File written: " + report)
    webbrowser.open(report)


def parse_input_file(filepath):
    title, file_data, inputfile_had_parts = inputfile.parse_data_file(filepath)
    my_data = []
    for data in file_data:
        filename = data[1]
        filepath = data[2]
        if not filename:
            filename = os.path.basename(filepath)
        my_data.append([filename, filepath])  # file title, filepath
    return title, my_data


def make_report(title, file_info_list, outfile, includepaths, force):
    for file_info in file_info_list:
        file_info.append(file_word_count(file_info[1]))
    return generate_report(title, file_info_list, outfile, includepaths, force)


''' date string with no spaces for timestamping files '''


def timestamp():
    # format the datetime without any spaces
    fmt = "%Y_%m_%d-%H_%M_%S"
    ct = dt.now().strftime(fmt)
    return str(ct)


''' human readable/useful date string'''


def date_string():

    date = dt.now()
    formatted_date = date.strftime("%B %d, %Y")

    time = dt.now()
    formatted_time = time.strftime("%I:%M:%S %p")

    return formatted_date + ", " + formatted_time


def file_contents(filepath):
    if not os.path.exists(filepath):
        raise Exception("{} doesn't exist"
                        .format(filepath))
    file = open(filepath, "r", encoding=ENC)
    file_str = file.read()
    file.close()
    return file_str


def write_file(filepath, data, force):
    if not os.path.isabs(filepath):
        raise Exception("Output file {} is not absolute!"
                        .format(filepath))
    if os.path.exists(filepath) and not force:
        raise Exception("Output file {} exists! "
                        "Use --FORCE / -F"
                        " to overwrite"
                        .format(filepath))
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


def generate_report(title, word_count_info, outfile, includepaths, force):

    date = date_string()

    contents = file_contents("report_template.html")

    contents = contents.replace('%title%', title)
    contents = contents.replace('%date%', date)

    soup = BeautifulSoup(contents.encode(ENC), 'html.parser')

    #table = soup.find("table", {"id":"table"})
    table = soup.find(attrs={'id': 'word-count-table'})

    total_words = 0
    for count_info in word_count_info:
        table.append(word_count_row(count_info, includepaths))
        total_words += count_info[2]
    table.append(word_count_row(["total", "", total_words],
                                includepaths, "total"))

    pretty_soup = soup.prettify(formatter='html')
    write_file(outfile, pretty_soup, force)
    return outfile


'''
takes a filepath on the filesystem
and returns a string that will open
it in the browser. i.e.
file:///C:/Users/Boris/file.txt
'''


def file_url(filepath):
    filestr = filepath.replace("\\", "/")
    filestr = "file:///" + filestr
    return filestr


def word_count_row(file_info, includepaths, row_id=None):
    return BeautifulSoup('''<tr id={}>
                         <td>{}</td>
                         <td><a href="{}" target=_blank>file</a></td>
                         <td>{} words</td>
                         </tr>'''
                         .format(row_id, file_info[0],
                                 file_url(file_info[1]),
                                 file_info[2]), 'html.parser')


def word_count_docx(filepath):
    document = Document(filepath)
    num_words = 0
    for paragraph in document.paragraphs:
        words = paragraph.text.split()
        num_words += len(words)
    return num_words


def word_count_txt(filepath):
    num_words = 0
    with open(filepath, 'r') as f:
        for line in f:
            words = line.split()
            num_words += len(words)
    return num_words


def file_word_count(filepath):

    if not os.path.exists(filepath):
        raise Exception("File {} does not exist!"
                        .format(filepath))

    extension = os.path.splitext(filepath)[1]
    if extension == ".txt":
        return word_count_txt(filepath)
    if extension == ".docx":
        return word_count_docx(filepath)
    else:
        raise Exception("invalid filetype {}. "
                        "Only .txt and .docx "
                        "currently supported"
                        .format(extension))


if __name__ == "__main__":
    main(sys.argv[1:])

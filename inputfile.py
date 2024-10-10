'''
A script for parsing an input file
and getting an cmd args and values
from it.
'''

#import config
import os

#logger = logging.getLogger(__name__)
#print = logger.info

'''
Raises exception with info
about line number, line, and
filepath to the inputfile
'''
def input_file_error(err_msg, line_number, input_filepath, line):
    raise Exception('''\n
Error Parsing INput file!
Error: {}

input file: {}
Line #    : {}
Line      : {}
'''.format(err_msg, input_filepath, line_number, line))


def check_if_value_blank(key, value, line_number, input_filepath, line):
    if not value:
        err_msg = "Found {} key but value was blank...".format(key)
        input_file_error(err_msg, line_number, input_filepath, line)
def validate_key_value(key, value, valid_values, line_number, input_filepath, line):
    if value not in valid_values:
        err_msg = '''
key '{}'...
\tValid values: {}
\tValue found : {}
\t(Note: make sure you are specifying it without quotes!)'''.format(key, ", ".join(valid_values), value)
        input_file_error(err_msg, line_number, input_filepath, line)

'''
Checks if line is a directive.
    i.e. line has format:
    [<directive name]
If so, returns the directive name
(in lower case)
If not, returns False
'''
def is_directive(line):
    line = line.strip()
    if line.startswith("[") and line.endswith("]"):
        line = line.lstrip("[")
        line = line.rstrip("]")
        line = line.strip()
        return line.lower()
    return False

'''
Parse a book data file.
Return title, and chapter info from
book directive.
'''
def parse_data_file(bookinput_filepath, start_chap_cnt_at=1):

    title = ""
    chapter_data = []
    found_part_data = False
    
    if not os.path.isabs(bookinput_filepath):
        raise Exception("Error! (from bookutils.py common lib): Path to book input is not absolute!")

    # get input file which has title and list of chapters and locations
    with open(bookinput_filepath, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

        chap_num_counter = start_chap_cnt_at
        part_num_counter = 0
        curr_part_name = ""
        curr_part_num = ""
        is_new_part = False
        line_num = 0
        chap_root = ""
        curr_directive = None
        found_book_directive = False
        for i, line in enumerate(lines):
            line_num += 1
            line = line.strip() # make sure this is before check for empty line!
            if not line or line.startswith("#"):
                continue

            # check if this is start of new directive
            directive = is_directive(line)
            if directive: # returns name of directive
                valid_directives = ["args", "keys", "book"]
                if directive not in valid_directives:
                    err_msg = "Found directive '{}', but this is not a valid directive.\nValid directives: {}".format(directive, ", ".join(valid_directives))
                    input_file_error(err_msg, line_num, bookinput_filepath, line)
                curr_directive = directive
                continue

            # check which directive you are on
            if curr_directive == "args": # cmd args... skip
                continue
            elif curr_directive == "keys": # root, title keys
                curr_key, curr_val = parse_key_directive_line(line, line_num, bookinput_filepath)
                if curr_key == "title":
                    title = curr_val
                    check_if_value_blank(curr_key, curr_val, line_num, bookinput_filepath, line)
                    continue
                if curr_key == "root":
                    chap_root = curr_val
                    check_if_value_blank(curr_key, curr_val, line_num, bookinput_filepath, line)
                    # if root wasn't absolute, convert it to absolute, rel dir inputfile is in
                    if not os.path.isabs(chap_root):
                        filedir = os.path.dirname(bookinput_filepath)
                        chap_root = os.path.normpath(os.path.abspath(os.path.join(filedir, chap_root)))
                    continue
                else:
                    valid_keys = ["title", "root"]
                    err_msg = '''
In [args] directive, found key: {}.
But, this is not a valid key.
Valid keys: {}'''.format(curr_key, ", ".join(valid_keys))
                    input_file_error(err_msg, line_num, bookinput_filepath, line)
            elif curr_directive == "book":
                found_book_directive = True
                # book derivative has started...
                # try to parse as a chapter line...
                # (has format <num>:<name>:filepath,
                # where <num> and <name> are optional)
                parse_line = line.split(":", 2)
                if len(parse_line) == 1:
                    # a new part. those lines are in format num ~ name (one can be blank)
                    parse_part_line = line.split("~")
                    if len(parse_part_line) == 2:
                        part_num = parse_part_line[0].strip()
                        part_name = parse_part_line[1].strip()
                        part_num_counter += 1
                        curr_part_name = part_name
                        curr_part_num = part_num
                        # need to pass this boolean back to make_chapters,
                        # because the ability to specify parts in the input file
                        # was added later... so needed to make it fit into
                        # existing logic... in order to do that, need
                        # to know a-priori if a chapter is the start of a new part.
                        # .. after this if block ends, it will go to next line,
                        # and so the next "chapter" (next line) will get flagged
                        # as being the first chapter of a new part
                        is_new_part = True
                        found_part_data = True
                        if not curr_part_num:
                            curr_part_num = str(part_num_counter)
                    else:
                        err_msg = '''
Can't parse line in [book] directive. This was NOT a chapter line, so assumed it was a part line.
Part lines have format <part num>~<part name>, but it was not in that format.'''
                        input_file_error(err_msg, line_num, bookinput_filepath, line)

                else:
                    if len(parse_line) < 3:
                        err_msg = '''
Can't parse line. Expecting format <chap #>:<chap title>:<filepath>,
but not enough ':' chars were found.
(You can omit chapter names and numbers, and the script will generate them
based on the order of the lines. But you will need two ':' on each line,
just keep blank space before first ':'\n
i.e. :myChap:/filepath/file.txt)'''
                        input_file_error(err_msg, line_num, bookinput_filepath, line)

                    chapnum = parse_line[0]
                    chapname = parse_line[1]
                    filepath = parse_line[2]
                    if not chapnum:
                        chapnum = str(chap_num_counter)
                    if not os.path.isabs(filepath) and chap_root:
                        # chapter root was specified;
                        # add filepath to it,
                        # UNLESS filepath is absolute
                        filepath = os.path.normpath(os.path.join(chap_root, filepath)) # need normpath or slashs might get mixed when you do os.path.join
                    if not os.path.isabs(filepath):
                        # check again if not abs,
                        # in case chap_root was specified
                        # and a new filepath was formed,
                        # but chap_root wasn't an abs path...
                        filedir = os.path.dirname(bookinput_filepath)
                        filepath = os.path.normpath(os.path.abspath(os.path.join(filedir, filepath)))

                    chapter_data.append([chapnum, chapname, filepath, curr_part_num, curr_part_name, is_new_part])
                    # reset is new part boolean (once you've set in chapter, the next chaptrs in this section
                    # won't be a new part...)
                    is_new_part = False
                    chap_num_counter += 1

    if not found_book_directive:
        raise Exception("Never found book directive in input file!")
    if not title:
        raise Exception("\nError: Did not find 'title' key in inputfile!")
    return title, chapter_data, found_part_data

'''
Takes an absolue path to a book input file.
Returns a dictionary with cmd args and
their values that were found in the input
file (if any)
'''
def parse_inputfile_arg_directive(bookinput_filepath):
    parsed_keys = {}
    if not os.path.isabs(bookinput_filepath):
        raise Exception("Can't parse input file at {} - not abs path".format(bookinput_filepath))
    if not os.path.exists(bookinput_filepath):
        raise Exception("Can't parse input file {} - file doesn't exist!".format(bookinput_filepath))

    with open(bookinput_filepath, 'r', encoding='utf-8-sig') as f: # readonly mode
        lines = f.readlines()
        curr_directive = None
        for i, line in enumerate(lines):
            line = line.strip() # make sure this is before check for empty line!
            if not line or line.startswith("#"):
                continue
            # check if this is start of new directive
            directive = is_directive(line)
            if directive: # returns name of directive
                curr_directive = directive
                continue
            # only care about 'args' directive
            if curr_directive == "args":
                curr_key, curr_val = parse_arg_directive_line(line, i+1, bookinput_filepath)
                if curr_val == "":
                    curr_val = True
                elif curr_val == "None":
                    curr_val = None
                parsed_keys[curr_key] = curr_val

    return parsed_keys

'''
Takes a string.
Removes whitespace, and any double or single quotes.
Also removes whitespace padding inside the double or single quotes.
'''
def strip_value(val):
    # strp whitespace AND surrounding qoutes
    val = val.strip()
    val = val.strip('"')
    val = val.strip("'")
    # strip whitespace again after removing any quotes
    return val.strip()

'''
Parses a line in the [args] directive

Format expected:
    --arg=value
        OR
    --arg (for boolean args)
Returns:
    arg, value
Examples:
    line: "--a=b" returns: "a", "b"
    line: "--a" returns "a", True
'''
def parse_arg_directive_line(line, line_number, inputfile_path):
    line = line.strip()
    key = None
    value = None
    if not line.startswith("--"):
        err_msg = "Line in [args] directive does NOT begin with -- !"
        input_file_error(err_msg, line_number, inputfile_path, line)

    parse_line = line.split("=", 1) # maxsplit 1 in case there's : chars in the value, such as 'root' directive
    key = parse_line[0].strip()
    # remove -- from start
    key = key[2:]
    # get value... if any...
    if len(parse_line) > 1:
        value = strip_value(parse_line[1])
    elif len(parse_line) == 1:
        # if no reesults from strip, it was a boolean arg
        # careful: will also end up with invalid delims
        # ex: --theme:a
        # it's wrong and it will end up just returning
        # "theme:a" as the key
        value = True

    return key, value

'''
Parses a line in the [keys] directive.

Format expected:
    key: value
Returns:
    key, value
Example:
    line: "title: My Book"
    Returns "title", "My Book"
'''
def parse_key_directive_line(line, i, bookinput_filepath):
    parse_line = line.split(":", 1) # maxsplit 1 in case there's : chars in the value, such as 'root' directive
    if len(parse_line) == 1:
        err_msg = '''
Trying to parse key and value from line in the [keys] directive.
Was expecting format:
    <key> : <value>
    (i.e. title: book title)
But there was no ':' char'''
        input_file_error(err_msg, i, bookinput_filepath, line)

    else:
        key = parse_line[0].strip()
        value = strip_value(parse_line[1])
        return key, value

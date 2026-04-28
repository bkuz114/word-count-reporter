# Help

`python word_count_reporter.py --help`

# Quickstart

## Install python dependencies

```
pip install beautifulsoup4
pip install-docx
```

Or, do so in a virtual env:

```
virtualenv testenv_1
.\testenv_1\scripts\activate (windows cmd)
source testenv_1/scripts/activate (git bash on windows)
pip install -r requirements.txt
```

one line:

`virtualenv testenv_1 && source testenv_1/scripts/activate && pip install -r requirements.txt`

## Run tool

`python word_count_reporter.py INPUT`

**Note**: Input is format of book builder input file.

# Example

An example using the included example intputfile / files. Creates a report with the word counts of these example files.

`python word_count_reporter.py example_inputfile.txt`

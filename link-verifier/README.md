# Link Verification Script

## Pre-Requisites

- Unix/Linux system
- Python3
- [pandoc](https://github.com/jgm/pandoc). Used to convert Markdown files to HTML, which are then searched.
- [GitHub CLI](https://github.com/cli/cli). Optional, but recommended to speed up the testing of links involving GitHub issues and pull requests.
- See [requirements.txt](requirements.txt) for versions of Python packages. This script uses beautfulsoup4, requests, and termcolor.

## Usage

```bash
python3 tools/link-verifier/verify-links.py -F [MARKDOWN_FILE_LIST] -L [URL_LIST]
```
The script will print URLs that were not accessible. For Markdown files, it will also test relative paths to files, and anchors within the same document.

### Allowlist

An allow list file contains a list of non-existent URLs used as placeholder examples in a repository.

### Example
Run the script with a list of space separated names of directories to exclude. Optionally increase verbosity to print all links.

```bash
./links-verifier/verify-links.py --test-markdown --exclude-dirs third-party cmock --include-file-types .c .h .dox --verbose
```
OR Run the script with a list of files (and/or) links that you want to test specifically. 

```bash
./links-verifier/verify-links.py --files README.md  --links https://mosquitto.org --verbose
```

## Command Line Options

The `--links` and `--include-file-types` options are mutually exclusive i.e. if the former is passed, then the script does not search for URLs in the repository, but if the latter is passed, then the script looks for URLs across the specified file type patterns in repository. If both options are passed, then `--links` will take precedence.
The  `--files` and `--test-markdown`  options are mutually exclusive i.e. if the former is passed, then the script tests links only in the passed list of files, but if the
latter is passed, then the script searches Markdown files and tests URLs, anchors and relative-file path in them. If both options are passed, then `--files` will take precedence.
The `--exclude-dirs` option is only relevant to the `--test-markdown` and `--include-file-types` options.

| Option | Argument | Description |
| --- | --- | --- |
| `-F`, `--files` | 1 or more space-separated filepaths | Filepaths to verify links. Filepaths may be absolute or relative. |
| `-L`, `--links` | 1 or more space-separated URLs | List of URLs to test. URLs should be separated by spaces. |
| `-M`, `--test-markdown` | *None* | Option to enable search and testing of Markdown files. |
| `-I`, `--include-file-types` | 1 or more space-separated file patterns | List of file patterns whose URLs will be tested. File Patterns should be separated by spaces. |
| `-D`, `--exclude-dirs` | 1 or more space-separated directory names | List of directories to ignore for Markdown files and URL search. Directories should be separated by spaces. |
| `-A`, `--allowlist-file` | Allowlist of URLs | Path to file containing list of URLs excused from link verification. |
| `-n`, `--num-processes` | Integer | Number of threads to run in parallel when generating HTML files from Markdown. Each link is still tested serially, however. |
| `-k`, `--keep` | *None* | Option to keep temporary HTML files instead of deleting them. Only useful for debugging. |
| `-v`, `--verbose` | *None* | Increase verbosity to print all files and links tested, instead of only errors. |

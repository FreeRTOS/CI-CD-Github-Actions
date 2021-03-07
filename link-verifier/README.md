# Link Verification Script

## Pre-Requisites

- Unix/Linux system
- Python3
- [pandoc](https://github.com/jgm/aapandoc). Used to convert Markdown files to HTML, which are then searched.
- [GitHub CLI](https://github.com/cli/cli). Optional, but recommended to speed up the testing of links involving GitHub issues and pull requests.
- See [requirements.txt](requirements.txt) for versions of Python packages. This script uses beautfulsoup4, requests, and termcolor.

## Usage

```bash
python3 tools/link-verifier/verify-links.py -F [MARKDOWN_FILE_LIST] -L [URL_LIST]
```
The script will print URLs that were not accessible. For Markdown files, it will also test relative paths to files, and anchors within the same document.

### Allowlist

[allowlist.txt](allowlist.txt) contains a list of non-existant URLs used as placeholder examples in this repository. The script does not use it, but it can be used to filter out URLs before passing them in.

### Example
Run the script with a list of space separated names of directories to exclude. Optionally increase verbosity to print all links.

```bash
./tools/link-verifier/verify-links.py -D third-party cmock  -v
```

## Command Line Options

| Option | Argument | Description |
| --- | --- | --- |
| `-D`, `--exclude-dirs` | 1 or more comma-separated directory names | List of directories to ignore. Directories should be separated by commas. |
| `-A`, `--allowlist-file` | Allowlist of URLs | Path to file containing list of URLs excused from link verification. |
| `-n`, `--num-processes` | Integer | Number of threads to run in parallel when generating HTML files from Markdown. Each link is still tested serially, however. |
| `-k`, `--keep` | *None* | Option to keep temporary HTML files instead of deleting them. Only useful for debugging. |
| `-v`, `--verbose` | *None* | Increase verbosity to print all files and links tested, instead of only errors. |

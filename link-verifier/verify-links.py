#!/usr/bin/env python3

import os
import sys
import time
import argparse
import re
import urllib
import subprocess
import requests
import shutil
from bs4 import BeautifulSoup
from termcolor import cprint
from multiprocessing import Pool
import traceback
from collections import defaultdict

THIS_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
TRUSTED_CA_BUNDLE = os.path.join(THIS_FILE_PATH, 'trusted_certs', 'ca_bundle.crt')

MARKDOWN_SEARCH_TERM = r"\.md$"
# Regex to find a URL
URL_SEARCH_TERM = r'(\b(https?)://[^\s\)\]\\"<>]+[^\s\)\.\]\\"<>])'
HTTP_URL_SEARCH_TERM = r'https?://'
# Some HTML tags that we choose to ignore
IGNORED_LINK_SCHEMES = r'mailto:|ftps?:|tel:|file:'
# Regexes to identify links to Github PRs or issues, which are very common in changelogs
# and may result in rate limiting if each link is fetched manually.
PULL_REQUEST_SEARCH = r'https://github.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/(\d+)$'
ISSUE_SEARCH = r'https://github.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/issues/(\d+)$'
# The value at which we should fetch all of a repo's PRs or issues rather than testing
# individually. It takes roughly half a second to test one link, and between 1/2 to 5
# seconds to fetch them all, depending on the size of the repo.
GITHUB_FETCH_THRESHOLD = 5

NUM_PR_KEY = 'num_prs'
NUM_IS_KEY = 'num_issues'
PR_KEY = 'prs'
ISSUE_KEY = 'issues'
PR_CACHED_KEY = 'pr_cached'
ISSUE_CACHED_KEY = 'issue_cached'
"""
Format for repository list:
{
    "owner/repository": {
        "num_prs": 0,           //Number of links that point to an issue in this repo.
        "num_issues": 0,        //Number of links that point to a PR in this repo.
        "pr_cached": True,      //Whether we've already fetched and cached PRs/issues.
        "issue_cached": True,
        "prs": (1,2,3),         //Cached set of PRs.
        "issues": (4,5,6)       //Cached set of issues.
    }
}
"""
main_repo_list = {}
# Whether to use the above cache of repositories.
use_gh_cache = True
# Track links so that we don't test multiple times.
link_cache = {}
# HTTP headers to user when making a request
http_headers = requests.utils.default_headers()

class HtmlFile:
    """A class of files with a .html extension"""

    def __init__(self, html_file_name):
        """Parse html in file and extract links and ids"""

        self.ids = []
        self.internal_links = []
        self.external_links = []
        self.name = html_file_name
        self.abspath = os.path.abspath(html_file_name)
        self.broken_links = []
        self.linked_repos = {}
        with open(html_file_name, 'r') as infile:
            html_data = infile.read()
        dirname = os.path.dirname(self.name)
        soup = BeautifulSoup(html_data, 'html.parser')
        # Find IDs. This is to check internal links within a file.
        for tag in soup.find_all(True, {'id': True}):
            self.ids.append(tag.get('id'))
        pr_search = re.compile(PULL_REQUEST_SEARCH)
        issue_search = re.compile(ISSUE_SEARCH)
        for tag in soup.find_all('a'):
            link = tag.get('href')
            if not re.search(HTTP_URL_SEARCH_TERM, link, re.IGNORECASE):
                if not re.search(IGNORED_LINK_SCHEMES, link, re.IGNORECASE):
                    if link is not None and link not in self.internal_links:
                        self.internal_links.append(link)
            else:
                if link is not None and link not in self.external_links:
                    self.external_links.append(link)
                    pr_match = pr_search.search(link)
                    if pr_match:
                        self.increment_gh_link_count(pr_match.group(1), pr_match.group(2), pr_match.group(3), True)
                    else:
                        issue_match = issue_search.search(link)
                        if issue_match:
                            self.increment_gh_link_count(issue_match.group(1), issue_match.group(2), issue_match.group(3), False)

    def increment_gh_link_count(self, owner, repo, num, is_pr):
        """Increment the count of links to Github PRs or issues"""

        repo_key = f'{owner}/{repo}'.lower()
        if repo_key not in self.linked_repos:
            self.linked_repos[repo_key] = { NUM_IS_KEY : 0, NUM_PR_KEY : 0 }
        if is_pr:
            self.linked_repos[repo_key][NUM_PR_KEY] += 1
        else:
            self.linked_repos[repo_key][NUM_IS_KEY] += 1

    def print_filename(self, filename, file_printed):
        """Prints a file name if it hasn't been printed before"""

        if not file_printed:
            print(f'FILE: {filename}')
        return True

    def identify_broken_links(self, files, verbose):
        """Tests links for existence"""

        dirname = os.path.dirname(self.name)
        # Only print the file name once
        file_printed = False
        for link in self.internal_links:
            # First, look for anchors in the same document.
            link_elements = link.split('#')
            path = link_elements[0]
            id = None
            if len(link_elements) > 1:
                id = link_elements[1]
            if path == '':
                if id is not None:
                    if id.lower() not in self.ids:
                        self.broken_links.append(link)
                        file_printed = self.print_filename(files[self.name], file_printed)
                        cprint(f'\tUnknown link: {link}', 'red')
                    elif verbose:
                        file_printed = self.print_filename(files[self.name], file_printed)
                        cprint(f'\t{link}', 'green')
                continue

            # At this point, this is probably a link to a file in the same repo,
            # so we test if the file exists.
            filename = os.path.join(dirname, path)
            absfile = os.path.abspath(filename)
            # Note: We don't test whether the link target exists, just the file.
            if not os.path.exists(absfile):
                self.broken_links.append(link)
                file_printed = self.print_filename(files[self.name], file_printed)
                cprint(f'\tUnknown file: {path}', 'red')
            elif verbose:
                file_printed = self.print_filename(files[self.name], file_printed)
                cprint(f'\t{link}','green')

        for link in self.external_links:
            # Remove the trailing slash or trailing coma
            if(link[-1] == "/" or link[-1] == ","):
                is_broken, status_code = test_url(link[:-1])
            else:
                is_broken, status_code = test_url(link)
            if is_broken:
                self.broken_links.append(link)
                file_printed = self.print_filename(files[self.name], file_printed)
                cprint(f'  {status_code}\t{link}', 'red')
            else:
                if verbose:
                    file_printed = self.print_filename(files[self.name], file_printed)
                    cprint(f'  {status_code}\t{link}', 'green')

def parse_file(html_file):
    """Parse href tags from an HTML file"""
    return HtmlFile(html_file)

def html_name_from_markdown(filename):
    md_pattern = re.compile(r"\.md$", re.IGNORECASE)
    return md_pattern.sub('.html', filename)

def create_html(markdown_file):
    """Use pandoc to convert a markdown file to an HTML file"""
    html_file = html_name_from_markdown(markdown_file)
    # Convert from Github-flavored Markdown to HTML
    cmd = f'pandoc -f gfm -o {html_file} {markdown_file}'
    # Use pandoc to generate HTML from Markdown
    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        encoding="utf-8",
        universal_newlines=True
    )
    return process

def issue_request(method, url, **kwargs):
    retries = 0

    while retries < 3:
        r = method(url, **kwargs)
        if r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", 60))
            time.sleep(retry_after)
            retries += 1
        else:
            return r
    raise Exception("Max retries exceeded")

def access_url(url):
    global http_headers
    status = ''
    is_broken = False
    try_with_trusted_ca_bundle = False

    try:
        r = issue_request(requests.head, url, allow_redirects=True, headers=http_headers)
        # Some sites may return 404 for head but not get, e.g.
        # https://tls.mbed.org/kb/development/thread-safety-and-multi-threading
        if r.status_code >= 400:
            # Allow redirects is already enabled by default for GET.
            r = issue_request(requests.get, url, headers=http_headers)

        if r.status_code >= 400:
            is_broken = True
        status = r.status_code
    except requests.exceptions.SSLError as e:
        print(str(e))
        try_with_trusted_ca_bundle = True
    except Exception as e:
        print(str(e))
        is_broken = True
        status = 'Error'

    if try_with_trusted_ca_bundle == True:
        try:
            r = issue_request(requests.head, url, allow_redirects=True, headers=http_headers, verify=TRUSTED_CA_BUNDLE)
            # Some sites may return 404 for head but not get, e.g.
            # https://tls.mbed.org/kb/development/thread-safety-and-multi-threading
            if r.status_code >= 400:
                # Allow redirects is already enabled by default for GET.
                r = issue_request(requests.get, url, headers=http_headers, verify=TRUSTED_CA_BUNDLE)

            if r.status_code >= 400:
                is_broken = True
            status = r.status_code
        except Exception as e:
            print(str(e))
            is_broken = True
            status = 'Error'

    # Use curl as a fallback.
    if is_broken == True:
        curl_cmd = f'curl -sIL -o /dev/null -w "%{{http_code}}" {url}'
        process = subprocess.run(
            curl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            encoding="utf-8",
            universal_newlines=True
        )
        http_status_code = int(process.stdout)
        if http_status_code == 200:
            is_broken = False
            status = http_status_code

    # Use urllib as a fallback.
    if is_broken == True:
        req = urllib.request.Request(url, headers=http_headers)
        try:
            response = urllib.request.urlopen(req)
            is_broken = False
            status = response.getcode()
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"urllib: {url} error: {e}")

    return is_broken, status

def test_url(url):
    """Tests a single url"""
    global use_gh_cache
    global main_repo_list
    global link_cache
    status = ''
    is_broken = False
    # Test if link was already tested before.
    if url in link_cache:
        return link_cache[url]
    # Test if link was cached in pre-fetched GitHub issues. If not, send a request for the link.
    if use_gh_cache:
        pr_match = re.search(PULL_REQUEST_SEARCH, url)
        issue_match = re.search(ISSUE_SEARCH, url)
        if pr_match is not None:
            repo_key = f'{pr_match.group(1)}/{pr_match.group(2)}'.lower()
            if repo_key in main_repo_list and PR_KEY in main_repo_list[repo_key]:
                if int(pr_match.group(3)) in main_repo_list[repo_key][PR_KEY]:
                    status = 'Good'
        elif issue_match is not None:
            repo_key = f'{issue_match.group(1)}/{issue_match.group(2)}'.lower()
            if repo_key in main_repo_list and ISSUE_KEY in main_repo_list[repo_key]:
                if int(issue_match.group(3)) in main_repo_list[repo_key][ISSUE_KEY]:
                    status = 'Good'
    if status != 'Good':
        is_broken, status = access_url(url)

    # Add result to cache so it won't be tested again.
    link_cache[url] = (is_broken, status)
    return is_broken, status

def fetch_issues(repo, issue_type, limit):
    """Uses the GitHub CLI to fetch a list of PRs or issues"""

    global use_gh_cache
    global main_repo_list
    if shutil.which('gh') is not None:
        # List PRs or issues for repository and extract numbers.
        cmd = f'gh {issue_type} list -R {repo} -s all -L {limit} | awk \'{{print $1}}\''
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            encoding="utf-8",
            universal_newlines=True
        )
        if process.returncode == 0:
            key = issue_type + 's'
            for issue in process.stdout.split():
                if(issue.isnumeric()):
                    main_repo_list[repo][key].add(int(issue))
                else:
                    raise TypeError(f"Attempted to cast {issue} as an int. Error fetching GitHub Issues")
        return 0
    else:
        use_gh_cache = False

def consolidate_repo_list(repo_list):
    """Combines each list of repos into a single main list"""

    global use_gh_cache
    global main_repo_list
    for repo, stats in repo_list.items():
        if repo not in main_repo_list:
            main_repo_list[repo] = stats
            main_repo_list[repo][PR_CACHED_KEY] = False
            main_repo_list[repo][ISSUE_CACHED_KEY] = False
            main_repo_list[repo][PR_KEY] = set()
            main_repo_list[repo][ISSUE_KEY] = set()
        else:
            main_repo_list[repo][NUM_PR_KEY] += stats[NUM_PR_KEY]
            main_repo_list[repo][NUM_IS_KEY] += stats[NUM_IS_KEY]
        # Fetch the list of GH PRs and cache them. If we run into an error then we
        # stop trying to use the cached list.
        if use_gh_cache:
            if main_repo_list[repo][NUM_PR_KEY] > GITHUB_FETCH_THRESHOLD and main_repo_list[repo][PR_CACHED_KEY] == False:
                try:
                    fetch_issues(repo, 'pr', 1500)
                except Exception as e:
                    traceback.print_exc()
                    use_gh_cache = False
                main_repo_list[repo][PR_CACHED_KEY] = True
            if main_repo_list[repo][NUM_IS_KEY] > GITHUB_FETCH_THRESHOLD and main_repo_list[repo][ISSUE_CACHED_KEY] == False:
                try:
                    fetch_issues(repo, 'issue', 1000)
                except Exception as e:
                    traceback.print_exc()
                    use_gh_cache = False
                main_repo_list[repo][ISSUE_CACHED_KEY] = True

def main():
    global http_headers
    parser = argparse.ArgumentParser(
        description='A script to test HTTP links, and all links in Markdown files.',
        epilog='Requires beautifulsoup4, requests, and termcolor from PyPi. ' +
               'Optional dependencies: pandoc (to support testing Markdown files), gh (To speed up checking GitHub links)'
    )
    parser.add_argument("-F", "--files", action="store", dest="files", nargs='+', help="List of Markdown files to test links in.")
    parser.add_argument("-L", "--links", action="store", dest="links", nargs='+', help="List of links to test.")
    parser.add_argument("-M", "--test-markdown", action="store_true", default=False, help="Enable search of Markdown files for testing links.")
    parser.add_argument("-D", "--exclude-dirs", action="store", dest="exclude_dirs", nargs='+', help="List of directories to ignore.")
    parser.add_argument("-I", "--include-file-types", action="store", dest="include_files", nargs='+', help="List of file patterns to search for URLs.")
    parser.add_argument("-A", "--allowlist-file", action="store", dest="allowlist", help="Path to file containing list of allowed URLs.")
    parser.add_argument("-n", "--num-processes", action="store", type=int, default=4, help="Number of processes to run in parallel")
    parser.add_argument("-k", "--keep", action="store_true", default=False, help="Keep temporary files instead of deleting")
    parser.add_argument("-u", "--user-agent", action="store", dest="user_agent", default=None, help="User agent to use for HTTP requests")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Print all links tested")
    args = parser.parse_args()

    html_file_list = []
    broken_links = []
    md_file_list = []
    link_set = set()
    link_to_files = defaultdict(set)
    exclude_dirs = [dir.lower() for dir in args.exclude_dirs] if args.exclude_dirs else []

    if args.user_agent != None:
        http_headers.update({ 'User-Agent': args.user_agent })

    if args.verbose:
        print("Using User-Agent: {}".format(http_headers['User-Agent']))

    # If any explicit files are passed, add them to md_file_list.
    if args.files is not None:
        md_file_list = args.files
    elif args.test_markdown:
        # Obtain list of Markdown files from the repository (along with excluding passed directories).
        for root, dirs, files in os.walk("./"):
            # Prune dirs to remove exclude directories, if passed as command line input, from search.
            dirs[:] = [dir for dir in dirs if dir.lower() not in exclude_dirs]
            md_file_list += [os.path.join(root, f) for f in files if re.search(MARKDOWN_SEARCH_TERM, f, re.IGNORECASE)]

    # If any explicit links are passed, add them to link_set.
    if args.links is not None:
        link_set = set(args.links)
    # Otherwise walk the file tree to discover links
    elif args.include_files is not None:
        for root, dirs, files in os.walk("./"):
            # Avoid exclude directories, if passed, from search.
            dirs[:] = [dir for dir in dirs if dir.lower() not in exclude_dirs]
            for file in files:
                if any(file.endswith(file_type) for file_type in args.include_files):
                    f_path = os.path.join(root, file)
                    if args.verbose:
                        print("\nProcessing File: {}".format(f_path))
                    with open(f_path, 'r', encoding="utf8", errors='ignore') as f:
                        # errors='ignore' argument Suppresses UnicodeDecodeError
                        # when reading invalid UTF-8 characters.
                        text = f.read()
                        urls = re.findall(URL_SEARCH_TERM, text)
                        for url in urls:
                            link_set.add(url[0])
                            link_to_files[url[0]].add(f_path)

    # If allowlist file is passed, add those links to link_cache so that link check on those URLs can be bypassed.
    if args.allowlist is not None:
        with open(args.allowlist, 'r') as file:
            for link in file.read().strip('\n').split('\n'):
                link_cache[link] = (False, 'Allowed')

    try:
        file_map = {}
        for f in md_file_list:
            process = create_html(f)
            if process.returncode != 0:
                cprint(process.stdout, 'red')
                print('Did you install pandoc?')
                sys.exit(process.returncode)
            html_file_list.append(html_name_from_markdown(f))
            # Create a map so that we know what file this was generated from.
            file_map[html_name_from_markdown(f)] = f

        # Parse files in parallel.
        pool = Pool(args.num_processes)
        file_objects = pool.map(parse_file, html_file_list)
        pool.close()
        pool.join()
        for file_obj in file_objects:
            consolidate_repo_list(file_obj.linked_repos)
        # Test links in series so we don't send too many HTTP requests in a short interval.
        for file_obj in file_objects:
            file_obj.identify_broken_links(file_map, args.verbose)
            broken_links += file_obj.broken_links
    # Remove the temporary files we created, especially if there was an exception.
    finally:
        for f in html_file_list:
            if not args.keep:
                os.remove(f)

    for link in link_set:
        if ( ( link[-1] == "/" ) or ( link[-1] == "," ) ):
            is_broken, status_code = test_url(link[:-1])
        else:
            is_broken, status_code = test_url(link)
        if is_broken:
            broken_links.append(link)
            print("FILES:", link_to_files[link])
            cprint(f'\t{status_code}\t{link}', 'red')
        else:
            if args.verbose:
                print("FILES:", link_to_files[link])
                cprint(f'\t{status_code}\t{link}', 'green')

    # Return code > 0 to return error.
    num_broken = len(broken_links)
    if num_broken > 0:
        print(f'{num_broken} broken link' + ('s', '')[num_broken == 1])
    sys.exit(num_broken != 0)

if __name__ == "__main__":
    main()

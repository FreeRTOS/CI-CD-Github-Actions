# Pre-requisites to running the spell check scripts

1. In your GNU environment, install the *spell* and *getopt* programs. Use the following commands in Debian distributions, to install the packages (*getopt* is part of the `util-linux` package):
   ```shell
   apt-get install spell
   apt-get install util-linux
   ```

1. Add the folder containing the **spellings/tools/ablexicon**, **spellings/tools/extract-comments**, and **spellings/tools/find-unknown-comment-words** scripts to your system's PATH.
   ```shell
   export PATH=<REPO_ROOT>/spellings/tools:$PATH
   ```

# How to create a lexicon.txt for a new library.

1. Ensure there does not exist a file called "lexicon.txt" in your library's root directory. Run the following command to create a lexicon.txt for your library:
   ```shell
   find-unknown-comment-words -d /path/to/your/library/root > /path/to/your/library/root/lexicon.txt
   ```

1. Check the contents of */path/to/your/library/root/lexicon.txt* for any misspelled words. Fix them in your library's source code and delete them from the lexicon.txt.

# How to run for changes to an existing library.

1. If there exists a lexicon.txt in the library's root directory, run the following command:
   ```shell
   find-unknown-comment-words -d /path/to/your/library/root/lexicon.txt
   ```

1. Add any non-dictionary correctly spelled words to */path/to/your/library/root/lexicon.txt*. Fix any misspelled words in your code comment change.

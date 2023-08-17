# I am a test file to make sure the regex name replacement only replaces files
# that end in .md, not all files with md in their name.
# I also exit to make sure we skip files that don't end in .[c, h, dox, md, html]
# When using the default input
# Here are two links that exist
[verify-links.py](../../verify-links.py)
[CI-CD-Github-Actions](https://github.com/FreeRTOS/CI-CD-Github-Actions]

# Here's a link that doesn't exist that should cause us to fail if searched
# But since we aren't searched by default this broken link should not cause an error
[Incredible link](https://github.com/FreeRTOS/A-Repo-That-Wins-You-The-Lottery)

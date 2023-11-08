# I am a test file to make sure the regex name replacement only 
# replaces files that end in .md, not all files with md in their name.
# Here's a random link for it to test as well
[verify-links.py](../../verify-links.py)
[CI-CD-Github-Actions](https://github.com/FreeRTOS/CI-CD-Github-Actions)
# Test that it will find this url
https://www.google.com
# Test that it will find this url and drop the slash
https://www.google.com/
# Test that it will find this url by dropping the coma
https://www.google.com,

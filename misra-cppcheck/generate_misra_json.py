# FreeRTOS CI Tools
# Copyright (C) 2021 Amazon.com, Inc. or its affiliates.  All Rights Reserved.
#
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# https://www.FreeRTOS.org
# https://github.com/FreeRTOS
#

import json
import os
import re
import zipfile
from typing import Dict, List, Pattern
from urllib import request

misra_category_map: Dict[str, str] = {
    "misra-c2012-d1.1": "Required",
    "misra-c2012-d2.1": "Required",
    "misra-c2012-d3.1": "Required",
    "misra-c2012-d4.1": "Required",
    "misra-c2012-d4.2": "Advisory",
    "misra-c2012-d4.3": "Required",
    "misra-c2012-d4.4": "Advisory",
    "misra-c2012-d4.5": "Advisory",
    "misra-c2012-d4.6": "Advisory",
    "misra-c2012-d4.7": "Required",
    "misra-c2012-d4.8": "Advisory",
    "misra-c2012-d4.9": "Advisory",
    "misra-c2012-d4.10": "Required",
    "misra-c2012-d4.11": "Required",
    "misra-c2012-d4.12": "Required",
    "misra-c2012-d4.13": "Advisory",
    "misra-c2012-d4.14": "Required",
    "misra-c2012-1.1": "Required",
    "misra-c2012-1.2": "Advisory",
    "misra-c2012-1.3": "Required",
    "misra-c2012-2.1": "Required",
    "misra-c2012-2.2": "Required",
    "misra-c2012-2.3": "Advisory",
    "misra-c2012-2.4": "Advisory",
    "misra-c2012-2.5": "Advisory",
    "misra-c2012-2.6": "Advisory",
    "misra-c2012-2.7": "Advisory",
    "misra-c2012-3.1": "Required",
    "misra-c2012-3.2": "Required",
    "misra-c2012-4.1": "Required",
    "misra-c2012-4.2": "Advisory",
    "misra-c2012-5.1": "Required",
    "misra-c2012-5.2": "Required",
    "misra-c2012-5.3": "Required",
    "misra-c2012-5.4": "Required",
    "misra-c2012-5.5": "Required",
    "misra-c2012-5.6": "Required",
    "misra-c2012-5.7": "Required",
    "misra-c2012-5.8": "Required",
    "misra-c2012-5.9": "Advisory",
    "misra-c2012-6.1": "Required",
    "misra-c2012-6.2": "Required",
    "misra-c2012-7.1": "Required",
    "misra-c2012-7.2": "Required",
    "misra-c2012-7.3": "Required",
    "misra-c2012-7.4": "Required",
    "misra-c2012-8.1": "Required",
    "misra-c2012-8.2": "Required",
    "misra-c2012-8.3": "Required",
    "misra-c2012-8.4": "Required",
    "misra-c2012-8.5": "Required",
    "misra-c2012-8.6": "Required",
    "misra-c2012-8.7": "Advisory",
    "misra-c2012-8.8": "Required",
    "misra-c2012-8.9": "Advisory",
    "misra-c2012-8.10": "Required",
    "misra-c2012-8.11": "Advisory",
    "misra-c2012-8.12": "Required",
    "misra-c2012-8.13": "Advisory",
    "misra-c2012-8.14": "Required",
    "misra-c2012-9.1": "Mandatory",
    "misra-c2012-9.2": "Required",
    "misra-c2012-9.3": "Required",
    "misra-c2012-9.4": "Required",
    "misra-c2012-9.5": "Required",
    "misra-c2012-10.1": "Required",
    "misra-c2012-10.2": "Required",
    "misra-c2012-10.3": "Required",
    "misra-c2012-10.4": "Required",
    "misra-c2012-10.5": "Advisory",
    "misra-c2012-10.6": "Required",
    "misra-c2012-10.7": "Required",
    "misra-c2012-10.8": "Required",
    "misra-c2012-11.1": "Required",
    "misra-c2012-11.2": "Required",
    "misra-c2012-11.3": "Required",
    "misra-c2012-11.4": "Advisory",
    "misra-c2012-11.5": "Advisory",
    "misra-c2012-11.6": "Required",
    "misra-c2012-11.7": "Required",
    "misra-c2012-11.8": "Required",
    "misra-c2012-11.9": "Required",
    "misra-c2012-12.1": "Advisory",
    "misra-c2012-12.2": "Required",
    "misra-c2012-12.3": "Advisory",
    "misra-c2012-12.4": "Advisory",
    "misra-c2012-12.5": "Mandatory",
    "misra-c2012-13.1": "Required",
    "misra-c2012-13.2": "Required",
    "misra-c2012-13.3": "Advisory",
    "misra-c2012-13.4": "Advisory",
    "misra-c2012-13.5": "Required",
    "misra-c2012-13.6": "Mandatory",
    "misra-c2012-14.1": "Required",
    "misra-c2012-14.2": "Required",
    "misra-c2012-14.3": "Required",
    "misra-c2012-14.4": "Required",
    "misra-c2012-15.1": "Advisory",
    "misra-c2012-15.2": "Required",
    "misra-c2012-15.3": "Required",
    "misra-c2012-15.4": "Advisory",
    "misra-c2012-15.5": "Advisory",
    "misra-c2012-15.6": "Required",
    "misra-c2012-15.7": "Required",
    "misra-c2012-16.1": "Required",
    "misra-c2012-16.2": "Required",
    "misra-c2012-16.3": "Required",
    "misra-c2012-16.4": "Required",
    "misra-c2012-16.5": "Required",
    "misra-c2012-16.6": "Required",
    "misra-c2012-16.7": "Required",
    "misra-c2012-17.1": "Required",
    "misra-c2012-17.2": "Required",
    "misra-c2012-17.3": "Mandatory",
    "misra-c2012-17.4": "Mandatory",
    "misra-c2012-17.5": "Advisory",
    "misra-c2012-17.6": "Mandatory",
    "misra-c2012-17.7": "Required",
    "misra-c2012-17.8": "Advisory",
    "misra-c2012-18.1": "Required",
    "misra-c2012-18.2": "Required",
    "misra-c2012-18.3": "Required",
    "misra-c2012-18.4": "Advisory",
    "misra-c2012-18.5": "Advisory",
    "misra-c2012-18.6": "Required",
    "misra-c2012-18.7": "Required",
    "misra-c2012-18.8": "Required",
    "misra-c2012-19.1": "Mandatory",
    "misra-c2012-19.2": "Advisory",
    "misra-c2012-20.1": "Advisory",
    "misra-c2012-20.2": "Required",
    "misra-c2012-20.3": "Required",
    "misra-c2012-20.4": "Required",
    "misra-c2012-20.5": "Advisory",
    "misra-c2012-20.6": "Required",
    "misra-c2012-20.7": "Required",
    "misra-c2012-20.8": "Required",
    "misra-c2012-20.9": "Required",
    "misra-c2012-20.10": "Advisory",
    "misra-c2012-20.11": "Required",
    "misra-c2012-20.12": "Required",
    "misra-c2012-20.13": "Required",
    "misra-c2012-20.14": "Required",
    "misra-c2012-21.1": "Required",
    "misra-c2012-21.2": "Required",
    "misra-c2012-21.3": "Required",
    "misra-c2012-21.4": "Required",
    "misra-c2012-21.5": "Required",
    "misra-c2012-21.6": "Required",
    "misra-c2012-21.7": "Required",
    "misra-c2012-21.8": "Required",
    "misra-c2012-21.9": "Required",
    "misra-c2012-21.10": "Required",
    "misra-c2012-21.11": "Required",
    "misra-c2012-21.12": "Advisory",
    "misra-c2012-21.13": "Mandatory",
    "misra-c2012-21.14": "Required",
    "misra-c2012-21.15": "Required",
    "misra-c2012-21.16": "Required",
    "misra-c2012-21.17": "Mandatory",
    "misra-c2012-21.18": "Mandatory",
    "misra-c2012-21.19": "Mandatory",
    "misra-c2012-21.20": "Mandatory",
    "misra-c2012-22.1": "Required",
    "misra-c2012-22.2": "Mandatory",
    "misra-c2012-22.3": "Required",
    "misra-c2012-22.4": "Mandatory",
    "misra-c2012-22.5": "Mandatory",
    "misra-c2012-22.6": "Mandatory",
    "misra-c2012-22.7": "Required",
    "misra-c2012-22.8": "Required",
    "misra-c2012-22.9": "Required",
    "misra-c2012-22.10": "Required",
}

request.urlretrieve(
    "https://gitlab.com/MISRA/MISRA-C/MISRA-C-2012/Example-Suite/-/archive/V2.1/Example-Suite-V2.1.zip",
    "misra_test_suite.zip",
)

file_path_regex: Pattern = re.compile(
    r"misra_test_suite\.zip/Example-Suite-V2\.1/(D|R)_(\d{1,2})_(\d{1,2})(?:_\d)?\.c"
)

misra_guideline_description_regex: Pattern = re.compile(
    r"/\*\n\s+\*\s+(D|R)\.(\d\d?).(\d\d?)\n\s\*\n\s((?:\*.*\n\s)+)\*/"
)

multiple_whitespace_regex: Pattern = re.compile(r"\s{2,}")


def cleanup_rule_text(rule_text: str):
    # Remove * characters
    rule_text = rule_text.replace("*", "")

    # Exclude everything after "Note: "
    if "Note: " in rule_text:
        rule_text = rule_text.split(" Note: ")[0]

    # Strip beginning and ending whitespace.
    rule_text = rule_text.strip()

    # Combine multiple whitespace characters into a single space
    rule_text = re.sub(multiple_whitespace_regex, " ", rule_text)

    # Add a period at the end of the text
    rule_text = rule_text + "."

    return rule_text


with zipfile.ZipFile("misra_test_suite.zip", "r") as zip:
    guideline_map: Dict[str,Dict[str,str]] = dict()

    for misra_test_file in zipfile.Path(zip, "Example-Suite-V2.1/").iterdir():
        match = file_path_regex.match(str(misra_test_file))
        if match:
            with misra_test_file.open("r") as file:
                f_contents: bytes = file.read()
                match = misra_guideline_description_regex.search(f_contents)

                if match:
                    guideline: Dict[str, str] = dict()
                    if match[1] == "D":
                        guideline["id"] = "misra-c2012-d{}.{}".format(
                            int(match[2]), int(match[3])
                        )
                        guideline["type"] = "Directive"
                    elif match[1] == "R":
                        guideline["id"] = "misra-c2012-{}.{}".format(
                            int(match[2]), int(match[3])
                        )
                        guideline["type"] = "Rule"
                    else:
                        continue

                    guideline["section"] = str(int(match[2], base=10))
                    guideline["item"] = str(int(match[3], base=10))
                    guideline["description"] = cleanup_rule_text(match[4])
                    guideline["category"] = misra_category_map[guideline["id"]]
                    if guideline["id"] not in guideline_map:
                        guideline_map[guideline["id"]] = guideline

    with open("misra_rules.json", "w", encoding="utf-8") as output_f:
        guidelines: List[Dict[str, str]] = list(guideline_map.values())
        json.dump(guidelines, output_f, indent=4)
        output_f.write(os.linesep)

os.remove("misra_test_suite.zip")

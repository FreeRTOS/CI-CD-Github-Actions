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

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from glob import glob
from tempfile import mkstemp
from typing import Dict, List, Optional, Pattern, Set, TextIO
from xml.dom import minidom


@dataclass(frozen=True, eq=True)
class MisraDeviation:
    rule_section: int
    rule_num: int
    file_path: Optional[str]
    line_no: Optional[int]

    def __repr__(self):
        if not self.file_path and not self.line_no:
            str_value = "misra-c2012-{}.{}".format(self.rule_section, self.rule_num)

        elif self.file_path and self.line_no:
            str_value = "misra-c2012-{}.{}:{}:{}".format(
                self.rule_section, self.rule_num, self.file_path, self.line_no
            )
        else:
            str_value = None
        return str_value


@dataclass(frozen=True, eq=True)
class CppcheckError:
    error_id: str
    file_path: str
    line_no: int
    message: Optional[str]

    def __repr__(self):
        return "{}:{}: {}".format(self.file_path, self.line_no, self.error_id)


deviations_set: Set[MisraDeviation] = set()
deviations_map: Dict[str, MisraDeviation] = dict()
cc_error_list: List[CppcheckError] = list()


def cppcheck_do_misra(project_json_path: str, target_files_set: Set[str]):
    args: List[str] = ["cppcheck"]

    fid, out_file = mkstemp()
    os.close(fid)

    args.append("--project={}".format(project_json_path))
    args.append("--std=c89")
    args.append("--enable=all")
    args.append("--inconclusive")
    args.append("--suppress=unusedFunction")
    args.append("--xml")
    args.append("--addon=misra")
    args.append("--dump")
    args.append("--output-file={}".format(out_file))
    for file in target_files_set:
        args.append(file)

    logging.info("Calling: " + " ".join(args))
    subprocess.run(args)
    return out_file


cov_exclusion_regex: Pattern = re.compile(
    r"coverity\[misra_c_2012_rule_(\d{1,2})_(\d{1,2})_violation\]"
)
c_comment_token_regex: Pattern = re.compile(r"^\s*((\/\/)|(\/\*.*)|.*(\*\/))$")


def parse_inline_suppressions(file_path: str):
    dump_file_path: str = file_path + ".dump"

    logging.info("Processing File: {}".format(dump_file_path))

    doc = minidom.parse(dump_file_path)

    tokens = doc.documentElement.getElementsByTagName("tok")
    # for token in tokens:
    for i in range(len(tokens)):
        token_str = tokens[i].getAttribute("str")
        token = tokens[i]
        # Only match exceptions for the file itself.
        if token.getAttribute("fileIndex") == "0":
            match = cov_exclusion_regex.search(token_str)
            if match:
                for j in range(i, len(tokens)):
                    token = tokens[j]
                    token_str = token.getAttribute("str")
                    # Skip tokens containing c comments (//, /*, */) or when determining line number
                    if c_comment_token_regex.search(token_str):
                        continue
                    else:
                        line_no = token.getAttribute("linenr")
                        deviation = MisraDeviation(
                            rule_section=int(match.group(1)),
                            rule_num=int(match.group(2)),
                            file_path=file_path,
                            line_no=int(line_no),
                        )

                        logging.info(
                            "Adding MISRA Rule {}.{} deviation at: {}:{} ".format(
                                deviation.rule_section,
                                deviation.rule_num,
                                deviation.file_path,
                                deviation.line_no,
                            )
                        )
                        deviations_map[str(deviation)] = deviation
                        break


# Coverity configs are in a variant of json which may include comments.
def parse_coverity_config(file_path: str):
    config_regex = re.compile(r"deviation:\s*\"Rule\s*(\d{1,2}).(\d{1,2})\"")
    with open(file_path, "r") as config_file:
        for line in config_file.readlines():
            match = config_regex.search(line.strip())
            if match:
                deviation = MisraDeviation(
                    rule_section=int(match.group(1)),
                    rule_num=int(match.group(2)),
                    file_path=None,
                    line_no=None,
                )
                deviations_map[str(deviation)] = deviation


def filter_cppcheck_output(
    base_directory: str, cppcheck_out_path: str, target_files_set: Set[str]
):
    cc_out = minidom.parse(cppcheck_out_path)
    cc_errors = cc_out.documentElement.getElementsByTagName("error")
    for error in cc_errors:
        locations = error.getElementsByTagName("location")
        if len(locations):
            file_path = os.path.relpath(
                os.path.realpath(locations[0].getAttribute("file")),
                start=base_directory,
            )
            line_no = locations[0].getAttribute("line")
        else:
            file_path = ""
            line_no = 0
        error_id = error.getAttribute("id")

        if "misra" in error_id:
            message = None
        else:
            message = error.getAttribute("msg")

        if file_path not in target_files_set:
            continue

        error_id_full = "{}:{}:{}".format(error_id, file_path, line_no)

        if error_id_full in deviations_map:
            logging.info("Applying specific deviation for {}".format(error_id_full))
        elif error_id in deviations_map:
            logging.info("Applying global deviation for {}".format(error_id_full))
        else:
            error = CppcheckError(
                error_id=error_id, file_path=file_path, line_no=line_no, message=message
            )
            cc_error_list.append(error)


def main():
    parser = argparse.ArgumentParser(
        "Parse c files for coverity-style inline exceptions. Also parse a coverify configuration file for global exclusions. Run cppcheck with the MISRA extension and filter the resulting misra warnings accordingly."
    )
    parser.add_argument(
        "-c",
        "--coverity-config",
        action="store",
        help="coverity-format project configuration file",
        default=None,
    )
    parser.add_argument(
        "-p",
        "--compile-commands",
        action="store",
        help="Path to the cmake genrated compile_commands.json file",
        default=None,
    )
    parser.add_argument(
        "-b",
        "--base-directory",
        action="store",
        help="Base directory path (defaults to CWD).",
        default=os.getcwd(),
    )
    parser.add_argument(
        "files", metavar="FILE", help="Target files to check (python regex)", nargs="+"
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    base_directory: str = os.path.realpath(args.base_directory)

    if not args.coverity_config or not os.path.exists(args.coverity_config):
        logging.error(
            "Configuration file: {} does not exist.".format(args.coverity_config)
        )
        sys.exit(1)

    parse_coverity_config(args.coverity_config)

    if not args.compile_commands or not os.path.exists(args.compile_commands):
        logging.error(
            "Compile Commands file: {} does not exist.".format(args.compile_commands)
        )
        sys.exit(1)

    target_files_set: Set[str] = set()

    if not args.files:
        target_files_set.update(
            glob(os.path.join(base_directory, "**"), recursive=True)
        )
    else:
        for file_glob in args.files:
            file_list = glob(os.path.join(base_directory, file_glob), recursive=True)
            if len(file_list) > 0:
                for file_path in file_list:
                    target_files_set.add(
                        os.path.relpath(
                            os.path.realpath(file_path), start=base_directory
                        )
                    )

    cc_files_set: Set[str] = set()
    with open(args.compile_commands, "r") as cc_file:
        cc_contents = json.load(cc_file)
        for target_f in cc_contents:
            f_path: str = os.path.relpath(
                os.path.realpath(target_f["file"]), start=base_directory
            )
            cc_files_set.add(f_path)

    target_files_set = set.intersection(target_files_set, cc_files_set)

    # Run cppcheck with misra module
    cc_out_file: str = cppcheck_do_misra(args.compile_commands, target_files_set)

    for target_file in target_files_set:
        parse_inline_suppressions(target_file)

    # Parse cppcheck output file
    filter_cppcheck_output(base_directory, cc_out_file, target_files_set)

    rule_text: Optional[Dict[str, str]]
    if os.access("misra_rules.json", os.R_OK):
        with open("misra_rules.json", "r") as file:
            misra_json = json.load(file)
            rule_text = dict()
            for rule in misra_json:
                rule_text[rule["id"]] = rule

    for error in cc_error_list:
        if error.file_path in target_files_set:
            print(error)
            text = None
            if rule_text:
                text = rule_text.get(error.error_id, None)
            if text:
                print(
                    "\t{}: {}".format(
                        text.get('category', "Unknown"),
                        text.get('description', 'Unknown'),
                    )
                )
            elif error.message:
                print("\t" + error.message)
            print()


if __name__ == "__main__":
    main()

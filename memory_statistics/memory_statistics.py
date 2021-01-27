#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess
import json
from collections import defaultdict


__TABLE_HEADER__ = "Code Size of {} (example generated with GCC for ARM Cortex-M)"
__THIS_FILE_PATH__ = os.path.dirname(os.path.abspath(__file__))


def make(sources, includes, flags, opt):
    args = ['make', '-B', '-f', os.path.join(__THIS_FILE_PATH__, 'makefile')]

    cflags = f'-O{opt}'
    for inc_dir in includes:
        cflags += ' -I "'+os.path.abspath(inc_dir)+'"'
    for flag in flags:
        cflags += f' -D {flag}'

    args += ['CFLAGS=' + cflags]
    args += ['SRCS=' + " ".join(sources)]

    proc = subprocess.Popen(args, stdout=subprocess.PIPE, universal_newlines=True)
    (results, _) = proc.communicate()
    print(results)

    args = ['make', '-f', os.path.join(__THIS_FILE_PATH__, 'makefile'), 'clean']
    args += ['SRCS=' + " ".join(sources)]
    proc = subprocess.Popen(args)

    return results


def convert_size_to_kb(byte_size):
    kb_size = round(int(byte_size)/1024,1)
    if (kb_size == 0.0):
        return 0.1
    else:
        return kb_size


def parse_make_output(output, values, key):
    '''
    output expects the output of the makefile, which ends in a call to
    arm-none-eabi-size The output of size is expected to be the Berkley output
    format: text data bss dec hex filename

    values is an input defaultdict which maps filenames to dicts of opt level
    to sizes. This function adds each file's size to the file's dict with the
    key provided by the key parameter.
    '''
    output = output.splitlines()

    # Skip to size output
    while output:
        line = output[0]
        output = output[1:]
        if line.startswith('arm-none-eabi-size'):
            break
    # Skip header
    output = output[1:]

    for line in output:
        parts = line.split()

        # parts[5] is the filename
        filename = os.path.basename(parts[5])
        filename = str(filename.replace('.o','.c').strip())

        if "3rdparty" in parts[5]:
            filename += " (third-party utility)"

        # parts[0] is the text size
        text_size = parts[0].strip()
        text_size_in_kb = convert_size_to_kb(text_size)

        values[filename][key] = text_size_in_kb


def parse_to_table(o1_output, os_output, name):
    sizes = defaultdict(dict)
    parse_make_output(o1_output, sizes, 'O1')
    parse_make_output(os_output, sizes, 'Os')

    table  ='<table>\n'
    table +='    <tr>\n'
    table +='        <td colspan="3"><center><b>{}</b></center></td>\n'.format(__TABLE_HEADER__.format(name))
    table +='    </tr>\n'
    table +='    <tr>\n'
    table +='        <td><b>File</b></td>\n'
    table +='        <td><b><center>With -O1 Optimization</center></b></td>\n'
    table +='        <td><b><center>With -Os Optimization</center></b></td>\n'
    table +='    </tr>\n'

    for f in sizes:
        table +='    <tr>\n'
        table +='        <td>{}</td>\n'.format(f)
        table +='        <td><center>{:.1f}K</center></td>\n'.format(sizes[f]['O1'])
        table +='        <td><center>{:.1f}K</center></td>\n'.format(sizes[f]['Os'])
        table +='    </tr>\n'

    table +='    <tr>\n'
    table +='        <td><b>Total estimates</b></td>\n'
    table +='        <td><b><center>{:.1f}K</center></b></td>\n'.format(sum(sizes[f]['O1'] for f in sizes))
    table +='        <td><b><center>{:.1f}K</center></b></td>\n'.format(sum(sizes[f]['Os'] for f in sizes))
    table +='    </tr>\n'
    table +='</table>\n'

    return table


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', required=True, help='Configuration json file for memory estimation.')
    parser.add_argument('-o', '--output', default=None, help='File to save generated size table to.')

    return vars(parser.parse_args())


def main():
    args = parse_arguments()

    '''
    Config file should contain a json object with the following keys:
      "lib_name": Name to use for the library in the table header
      "src": Array of source paths to measure sizes of
      "include": Array of include directories
      "compiler_flags": (optional) Array of extra flags to use for compiling
    '''
    with open(args['config']) as config_file:
        config = json.load(config_file)

    if "lib_name" not in config:
        print("Error: Config file is missing \"lib_name\" key.")
        sys.exit(1)

    if "src" not in config:
        print("Error: Config file is missing \"src\" key.")
        sys.exit(1)

    if "include" not in config:
        print("Error: Config file is missing \"include\" key.")
        sys.exit(1)

    if "compiler_flags" not in config:
        config["compiler_flags"] = []

    o1_output = make(config['src'], config['include'], config['compiler_flags'], '1')
    os_output = make(config['src'], config['include'], config['compiler_flags'], 's')

    table = parse_to_table(o1_output, os_output, config['lib_name'])

    print(table)

    if args['output']:
        with open(args['output'], 'w') as output:
            output.write(table)

if __name__ == '__main__':
    main()

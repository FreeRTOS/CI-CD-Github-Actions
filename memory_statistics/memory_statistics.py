#!/usr/bin/env python3

import os
import sys
import shutil
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

    # Run `make clean` to remove object files generated during previous make invocation.
    # This is so that memory_statistics.py cleans up after itself when running it locally.
    args = ['make', '-f', os.path.join(__THIS_FILE_PATH__, 'makefile'), 'clean']
    args += ['SRCS=' + " ".join(sources)]
    proc = subprocess.Popen(args)

    return results


def convert_size_to_kb(byte_size):
    kb_size = round(byte_size/1024,1)
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
        text_size = int(parts[0].strip())
        # parts[1] is the data size
        data_size = int(parts[1].strip())

        total_size_in_kb = convert_size_to_kb(text_size + data_size)

        values[filename][key] = total_size_in_kb

def parse_to_object(o1_output, os_output, name):
    sizes = defaultdict(dict)
    parse_make_output(o1_output, sizes, 'O1')
    parse_make_output(os_output, sizes, 'Os')

    ret = {
            "table_header": __TABLE_HEADER__.format(name),
            "column_header": {
                "files_column_header": "File",
                "files_o1_header": "With -O1 Optimization",
                "files_os_header": "With -Os Optimization",
                },
            "files": [],
            "total": {
                "total_header": "Total estimates",
                "total_o1": '{:.1f}K'.format(sum(sizes[f]['O1'] for f in sizes)),
                "total_os": '{:.1f}K'.format(sum(sizes[f]['Os'] for f in sizes)),
                }
            }

    for f in sizes:
        ret["files"].append({
            "file_name": f,
            "o1_size": '{:.1f}K'.format(sizes[f]['O1']),
            "os_size": '{:.1f}K'.format(sizes[f]['Os'])
        })

    return ret

def generate_table_from_object(estimate):
    table  ='<table>\n'
    table +='    <tr>\n'
    table +='        <td colspan="3"><center><b>{}</b></center></td>\n'.format(estimate['table_header'])
    table +='    </tr>\n'
    table +='    <tr>\n'
    table +='        <td><b>{}</b></td>\n'.format(estimate['column_header']['files_column_header'])
    table +='        <td><b><center>{}</center></b></td>\n'.format(estimate['column_header']['files_o1_header'])
    table +='        <td><b><center>{}</center></b></td>\n'.format(estimate['column_header']['files_os_header'])
    table +='    </tr>\n'

    for f in estimate['files']:
        table +='    <tr>\n'
        table +='        <td>{}</td>\n'.format(f['file_name'])
        table +='        <td><center>{}</center></td>\n'.format(f['o1_size'])
        table +='        <td><center>{}</center></td>\n'.format(f['os_size'])
        table +='    </tr>\n'

    table +='    <tr>\n'
    table +='        <td><b>{}</b></td>\n'.format(estimate['total']['total_header'])
    table +='        <td><b><center>{}</center></b></td>\n'.format(estimate['total']['total_o1'])
    table +='        <td><b><center>{}</center></b></td>\n'.format(estimate['total']['total_os'])
    table +='    </tr>\n'
    table +='</table>\n'

    return table

def validate_library_config(config):
    '''
    Config file should contain a json object with the following keys:
      "lib_name": Name to use for the library in the table header
      "src": Array of source paths to measure sizes of
      "include": Array of include directories
      "compiler_flags": (optional) Array of extra flags to use for compiling
    '''
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

def generate_library_estimates(config_path):
    with open(config_path) as config_file:
        config = json.load(config_file)

    validate_library_config(config)

    o1_output = make(config['src'], config['include'], config['compiler_flags'], '1')
    os_output = make(config['src'], config['include'], config['compiler_flags'], 's')

    return parse_to_object(o1_output, os_output, config['lib_name'])

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', required=True, help='Configuration json file for memory estimation.')
    parser.add_argument('-o', '--output', default=None, help='File to save generated size table to.')
    parser.add_argument('-j', '--json_report', action='store_true', help='Output a report for multiple libraries in JSON format.')

    return vars(parser.parse_args())

def main():
    args = parse_arguments()

    if not shutil.which("arm-none-eabi-gcc"):
        print("ARM GCC not found. Please add the ARM GCC toolchain to your path.")
        sys.exit(1)

    if not args['json_report']:
        lib_data = generate_library_estimates(args['config'])
        doc = generate_table_from_object(lib_data)

    else:
        with open(args['config']) as paths_file:
            libs = json.load(paths_file)

        doc = {}
        cwd = os.getcwd()

        for lib in libs:
            lib_path = libs[lib]['path']
            config_path = os.path.abspath(libs[lib].get('config',
                    os.path.join(lib_path, ".github/memory_statistics_config.json")))

            os.chdir(lib_path)
            doc[lib] = generate_library_estimates(config_path)
            os.chdir(cwd)

        doc = json.dumps(doc, sort_keys=False, indent=4)

    print(doc)

    if args['output']:
        with open(args['output'], 'w') as output:
            output.write(doc)

if __name__ == '__main__':
    main()

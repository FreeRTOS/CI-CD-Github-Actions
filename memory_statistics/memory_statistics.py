#!/usr/bin/env python3

import os
import argparse
import subprocess
from collections import defaultdict


__TABLE_HEADER__ = "Code Size of {} (example generated with GCC for ARM Cortex-M)"
__THIS_FILE_PATH__ = os.path.dirname(os.path.abspath(__file__))


def make(sources, includes, flags, opt):
    args = ['make', '-B', '-f', __THIS_FILE_PATH__ + '/makefile']

    cflags = f'-O{opt} -I "{__THIS_FILE_PATH__ + "/config_files"}"'
    for inc_dir in includes.splitlines():
        cflags += ' -I "'+os.path.abspath(inc_dir)+'"'
    for flag in flags.splitlines():
        cflags += f' -D {flag}'

    args += ['CFLAGS=' + cflags]
    args += ['SRCS=' + " ".join(sources.splitlines())]

    proc = subprocess.Popen(args, stdout=subprocess.PIPE, universal_newlines=True)
    (results, _) = proc.communicate()
    print(results)

    return results


def convert_size_to_kb(byte_size):
    kb_size = round(int(byte_size)/1024,1)
    if (kb_size == 0.0):
        return 0.1
    else:
        return kb_size


def parse_make_output(output, values, key):
    '''
    It assumes the Berkley output format:
    text       data     bss     dec     hex filename

    Values is defaultdict mapping filenames to dicts
    This adds each file's size to the dict in its entry under the provided key.
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

        filename = os.path.basename(parts[5])
        filename = str(filename.replace('.o','.c').strip())

        if "3rdparty" in parts[5]:
            filename += " (third-party utility)"

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

    parser.add_argument('-n', '--name', required=True, help='Library name for table header.')
    parser.add_argument('-s', '--sources', required=True, help='Files to measure size of.')
    parser.add_argument('-i', '--includes', required=True, help='Include directories.')
    parser.add_argument('-f', '--flags', default='', help='Extra compiler flags.')
    parser.add_argument('-o', '--output', default=None, help='File to save generated size table to.')

    return vars(parser.parse_args())


def main():
    args = parse_arguments()

    o1_output = make(args['sources'], args['includes'], args['flags'], '1')
    os_output = make(args['sources'], args['includes'], args['flags'], 's')

    table = parse_to_table(o1_output, os_output, args['name'])

    print(table)

    if args['output']:
        with open(args['output'], 'w') as output:
            output.write(table)

if __name__ == '__main__':
    main()

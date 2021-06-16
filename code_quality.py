#!/usr/bin/env python

"""
Run code quality checks and code formatters on a Git repository.

Only files which changed since a given branch or commit are processed.
"""

import argparse
from pathlib import Path
import re
import subprocess
import sys


CPP_EXTENSIONS = ('.cpp', '.cc', '.cxx', '.hpp', '.hh', '.hxx', '.h')
PY_EXTENSIONS = ('.py',)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--py', action='store_true', default=False,
                        help='Enable all Python checks')
    parser.add_argument('--yapf', nargs='?', default=None, const='yapf',
                        help='Reformat Python files')
    parser.add_argument('--flake8', nargs='?', default=None, const='flake8',
                        help='Check Python files with flake8')
    parser.add_argument('--cpp', action='store_true', default=False,
                        help='Enable all C++ checks')
    parser.add_argument('--clang-format', nargs='?', default=None, const='clang-format',
                        help='Reformat C++ code')
    parser.add_argument('--ref', default='main',
                        help='Name / hash of the reference branch / commit')
    parser.add_argument('--prefix', metavar='NUM', default=0,
                        help='Strip this number of directories from file paths')
    args = parser.parse_args()
    if not any((args.py, args.yapf, args.flake8, args.cpp)):
        print('WARNING no checkers are enabled.')
    if args.py:
        if not args.yapf:
            args.yapf = 'yapf'
        if not args.flake8:
            args.flake8 = 'flake8'
    if args.cpp:
        if not args.clang_format:
            args.clang_format = 'clang-format'
    return args


def call_pipe(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True).stdout.decode('utf-8').strip()


def find_repo_root():
    try:
        return call_pipe(['git', 'rev-parse', '--show-toplevel'])
    except subprocess.CalledProcessError:
        print('Failed to determine git root directory. Is this a git repository?')
        sys.exit(1)


def get_diff(repo_root, ref):
    current_branch = call_pipe(['git', 'branch', '--show-current'], cwd=repo_root)
    base_commit = call_pipe(['git', 'merge-base', ref, current_branch], cwd=repo_root)
    return call_pipe(['git', 'diff', '-U0', '--no-color', '--relative', base_commit], cwd=repo_root)


def parse_diff(diff, n_path_strip):
    filename_regex = re.compile(rf'^\+\+\+ (.*?/){{{n_path_strip}}}(\S*)')
    lineno_regex = re.compile(r'^@@.*?\+(\d+)(,(\d+))?')
    lines = dict()
    current_file = None

    for line in diff.splitlines():
        match = filename_regex.match(line)
        if match:
            current_file = Path(match[2])
        if current_file is None:
            continue   # did not find a file yet or file name is empty

        match = lineno_regex.match(line)
        if match:
            start_line = int(match[1])
            n_lines = int(match[3]) if match[3] else 1
            if n_lines == 0:
                continue
            end_line = start_line + n_lines
            lines.setdefault(current_file, []).append(slice(start_line, end_line, 1))

    return lines


def run_formatter(cmd, modified_lines, extensions, line_separator):
    for fname, lines in filter(lambda t: t[0].suffix in extensions, modified_lines.items()):
        subprocess.check_call([cmd, str(fname), '-i', *[f'--lines={l.start}{line_separator}{l.stop}' for l in lines]])


def run_flake8(cmd, modified_lines):
    for fname in filter(lambda fn: fn.suffix in PY_EXTENSIONS, modified_lines):
        subprocess.run([cmd, str(fname)])


def main():
    args = parse_args()
    repo_root = find_repo_root()
    diff = get_diff(repo_root, args.ref)
    modified_lines = parse_diff(diff, args.prefix)

    if args.clang_format:
        run_formatter(args.clang_format, modified_lines, CPP_EXTENSIONS, ':')
    if args.yapf:
        run_formatter(args.yapf, modified_lines, PY_EXTENSIONS, '-')
    if args.flake8:
        run_flake8(args.flake8, modified_lines)


if __name__ == '__main__':
    main()

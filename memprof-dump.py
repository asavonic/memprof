#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2016 Andrew Savonichev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Use memprof_dump to dump .alloc or .info files produces by memprof collector

Usage:
    memprof_dump --alloc <file>
    memprof_dump --info <file>
    memprof_dump (-h | --help)

Options
    --alloc     read .alloc file - allocation and dealocation information
    --info      read .info file - system data, shared libraries information
    -h|--help   show this message
"""
from docopt import docopt
from memprof import read_alloc_stream


def dump_alloc(f):
    for entry in read_alloc_stream(f):
        print(entry.dump())


def dump_info(f):
    raise RuntimeError("Unimplemented method: dump_info")


if __name__ == '__main__':
    args = docopt(__doc__, version='Naval Fate 2.0')
    with open(args["<file>"], "rb") as f:
        if args["--alloc"]:
            dump_alloc(f)
        elif args["--info"]:
            dump_info(f)

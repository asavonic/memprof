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

import os
import unittest
from subprocess import check_call
import memprof
from memprof import read_alloc_stream


tests_dir = "."


def run_memprof_exe(exe):
    check_call([exe])


class TestBasic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_exe = os.path.join(tests_dir, "test_basic")
        run_memprof_exe(cls.test_exe)
        cls.alloc_file = "test_basic.alloc"

        with open(cls.alloc_file, "rb") as f:
            cls.alloc_stream = [entry for entry in read_alloc_stream(f)]

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.alloc_file)
        os.remove(cls.alloc_file + "_ref")


    def test_id_unique(self):
        ids = {}
        for entry in TestBasic.alloc_stream:
            ids[entry.id] = True
        self.assertEqual(len(ids.keys()), len(TestBasic.alloc_stream))

    def test_memory_ptr(self):
        with open("test_basic.alloc_ref") as f:
            def ref_memptrs():
                for line in f.readlines():
                    yield int(line.split()[0], 16)

            for entry, memptr in zip(TestBasic.alloc_stream, ref_memptrs()):
                self.assertEqual(memptr, entry.memptr)

    def test_alloc_size(self):
        with open("test_basic.alloc_ref") as f:
            def ref_alloc_sizes():
                for line in f.readlines():
                    yield int(line.split()[1])

            for entry, size in zip(TestBasic.alloc_stream, ref_alloc_sizes()):
                self.assertEqual(size, entry.size)

    def test_alloc_types(self):
        ref_types = ["alloc"] * 3 + ["free"] * 3
        self.assertEqual(len(ref_types), len(TestBasic.alloc_stream))
        for entry, ref in zip(TestBasic.alloc_stream, ref_types):
            self.assertEqual(ref, entry.ty)

    def test_symbol_resolve(self):
        ref_stacks = [
            ["a", "main"],
            ["a", "b", "main"],
            ["a", "b", "c", "main"],
            ["cleanup", "main"],
            ["cleanup", "main"],
            ["cleanup", "main"]
        ]

        def resolve_name(frame):
            symbol = memprof.Symbol(frame.rel_addr, TestBasic.test_exe)
            return symbol.name

        def stacks_stream():
            for entry in TestBasic.alloc_stream:
                yield [resolve_name(f) for f in entry.backtrace]

        got_stacks = list(stacks_stream())

        self.assertEqual(len(ref_stacks), len(got_stacks))
        for got, ref in zip(got_stacks, ref_stacks):
            self.assertEqual(got[:len(ref)], ref)


if __name__ == '__main__':
    unittest.main()

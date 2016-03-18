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

import struct
import time
import textwrap
from subprocess import check_output


class FileFormatError(RuntimeError):
    pass

struct_types = {
    "size": "q",
    "uintptr": "q",
    "uint8": "B",
    "int32": "i"
}


def struct_read(format, f):
    st = struct.Struct(format)
    data = f.read(st.size)

    tup = st.unpack_from(data)
    if len(tup) == 1:
        return tup[0]
    else:
        return tup


class AllocEntry(object):
    def __init__(self):
        self.id = 0
        self.ty = "none"
        self.timestamp = time.gmtime(0)
        self.memptr = 0
        self.size = 0
        self.backtrace = []

    def _read_id(f):
        st = struct.Struct(struct_types["size"])
        id_data = f.read(st.size)
        if (len(id_data) < st.size):
            return None
        else:
            return st.unpack(id_data)[0]

    def from_file(f):
        entry = AllocEntry()
        entry.id = AllocEntry._read_id(f)
        if entry.id is None:
            return None

        int_type = struct_read(struct_types["uint8"], f)
        if (int_type == 1):
            entry.ty = "alloc"
        elif (int_type == 2):
            entry.ty = "free"
        else:
            raise FileFormatError("invalid type: " + str(int_type))

        str_time = struct_read(struct_types["int32"], f)
        entry.timestamp = time.gmtime(int(str_time))

        entry.memptr = struct_read(struct_types["uintptr"], f)
        entry.size = struct_read(struct_types["size"], f)

        num_frames = struct_read(struct_types["uint8"], f)
        entry.backtrace = [Frame.from_file(f) for i in range(0, num_frames)]

        return entry

    def dump(self):
        return textwrap.dedent("""
        id: {}
        type: {}
        timestamp: {}
        memptr: {}
        size: {}
        backtrace:
        {}
        """).format(
            self.id,
            self.ty,
            self.timestamp,
            hex(self.memptr),
            self.size,
            "\n".join([frame.dump() for frame in self.backtrace])
        )


class Frame(object):
    def __init__(self):
        self.module_base = 0
        self.rel_addr = 0

    def from_file(f):
        frame = Frame()
        frame.module_base = struct_read(struct_types["uintptr"], f)
        frame.rel_addr = struct_read(struct_types["uintptr"], f)
        return frame

    def dump(self):
        return "module: {}, addr: {}".format(
            hex(self.module_base), hex(self.rel_addr))


def read_alloc_stream(file):
    while True:
        entry = AllocEntry.from_file(file)
        if entry is None:
            return
        yield entry


class Symbol(object):
    def __init__(self, addr, module):
        self.addr = addr
        self.module = module

        output = check_output(["addr2line", "-f", "-e", module, str(hex(addr))])
        lines = output.decode('utf-8').split("\n")
        self.name, self.file = lines[0], lines[1]


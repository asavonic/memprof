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

import time
import json
import random

current_time = int(time.time())
random.seed(current_time)
memory = 100


def generate_memstamp():
    global memory
    global current_time
    current_time += random.randint(1, 5)

    memory += random.randint(-1, 1) * random.random() * 20
    if memory <= 0:
        memory += random.random() * 200

    backtrace = ["foo::baz()", "foo::bar()", "foo::foo()"]
    return {
        "x": current_time,
        "y": float("%.4f" % memory),
        "bt": backtrace,
        "id": 0xff
    }


memstamps = [generate_memstamp() for i in range(0, 1000)]
print(json.dumps([stamp for stamp in memstamps]))


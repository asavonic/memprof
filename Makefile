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

CC      = gcc
CFLAGS  = -g -std=c99 # -DMEMPROF_LOGGING_ON
LDFLAGS = -ldl
RM      = rm -f
PYTHON  = python

default: all

test: basic
	$(PYTHON) run-tests.py

basic: memprof.c tests/basic.c
	$(CC) $(CFLAGS) -I. memprof.c tests/basic.c $(LDFLAGS) -o test_basic

clean veryclean:
	$(RM) test_basic
	$(RM) test_basic.*

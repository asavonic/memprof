/* The MIT License (MIT)

Copyright (c) 2016 Andrew Savonichev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE. */

#include "memprof.h"
#include <stdlib.h>
#include <stdio.h>

void* a(int size) {
    void* mem = malloc(size);
    log_mem_alloc(mem, size);
    return mem;
}

void* b(int size) {
    return a(size);
}

void* c(int size) {
    return b(size);
}

void* cleanup(void* mem) {
    free(mem);
    log_mem_free(mem);
}

int main(int argc, char *argv[]) {
    g_memprof_alloc_filename = "test_basic.alloc";
    g_memprof_info_filename = "test_basic.info";

    FILE* ref_file = fopen("test_basic.alloc_ref", "w");

    void* a_ptr = a(10);
    fprintf(ref_file, "%p 10\n", a_ptr);

    void* b_ptr = b(20);
    fprintf(ref_file, "%p 20\n", b_ptr);

    void* c_ptr = c(30);
    fprintf(ref_file, "%p 30\n", c_ptr);

    cleanup(a_ptr);
    cleanup(b_ptr);
    cleanup(c_ptr);

    return 0;
}

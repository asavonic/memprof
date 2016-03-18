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

#include <stdint.h>
#include <stdio.h>
#include <time.h>
#include <assert.h>
#include <string.h>

#define __USE_GNU
#include <dlfcn.h>

#include <unwind.h>


#if defined(MEMPROF_LOGGING_ON)
	#define MEMPROF_LOG(...) printf(__VA_ARGS__)
#else
	#define MEMPROF_LOG(...)
#endif

typedef struct {
	uintptr_t module_base;
	size_t    name_size;
	const char*     name;
} module_info_t;

int create_module_info(module_info_t* info, uintptr_t addr) {
	Dl_info dl_info;
	int err = dladdr((void*) addr, &dl_info);
	if (err != 0) {
		return err;
	}

	info->module_base = (uintptr_t) dl_info.dli_fbase;
	info->name_size = strlen(dl_info.dli_fname);
	info->name = dl_info.dli_fname;

	return 0;
}

int module_info_size(const module_info_t* info) {
	return sizeof(info->module_base)
		+ sizeof(info->name_size)
		+ info->name_size;
}

int write_module_info(const module_info_t* info, FILE* f) {
	int written = 0;
	written = fwrite(&info->module_base, sizeof(info->module_base), 1, f);
	if (!written) return -1;

	written = fwrite(&info->name_size, sizeof(info->name_size), 1, f);
	if (!written) return -1;

	written = fwrite(&info->name, sizeof(info->name[0]), info->name_size, f);
	if (!written) return -1;

	return 0;
}

typedef struct {
	uintptr_t module_base;
	uintptr_t symbol_addr;
} stackframe_t;

typedef struct {
	size_t    id;
	int8_t    type;
	int32_t   timestamp;
	uintptr_t memptr;
	size_t    size;

	int8_t  num_frames;
	const stackframe_t* frames;
} alloc_desc_t;

int write_alloc_desc(const alloc_desc_t* desc, FILE* f) {
	int written = 0;
	written = fwrite(&desc->id, sizeof(desc->id), 1, f);
	if (!written) return -1;

	written = fwrite(&desc->type, sizeof(desc->type), 1, f);
	if (!written) return -1;

	written = fwrite(&desc->timestamp, sizeof(desc->timestamp), 1, f);
	if (!written) return -1;

	written = fwrite(&desc->memptr, sizeof(desc->memptr), 1, f);
	if (!written) return -1;

	written = fwrite(&desc->size, sizeof(desc->size), 1, f);
	if (!written) return -1;

	written = fwrite(&desc->num_frames, sizeof(desc->num_frames), 1, f);
	if (!written) return -1;

	written = 0;
	for (int i = 0; i < desc->num_frames; ++i) {
		const stackframe_t* frame = desc->frames + i;

		written += fwrite(&frame->module_base, sizeof(frame->module_base), 1, f);
		written += fwrite(&frame->symbol_addr, sizeof(frame->symbol_addr), 1, f);
	}

	if (written != desc->num_frames * 2) {
		return -1;
	}

	return 0;
}

int __addr_info(const void* addr, uintptr_t* module_base, uintptr_t* sym_addr) {
	Dl_info info;
	int err = dladdr(addr, &info);
	if (err != 0) {
		return err;
	}

	*module_base = (uintptr_t) info.dli_fbase;
	*sym_addr = (uintptr_t) info.dli_saddr;

	return 0;
}

typedef struct {
	stackframe_t* current;
	stackframe_t* end;
} __unwind_state_t;

_Unwind_Reason_Code __unwind_callback(struct _Unwind_Context* context, void* arg)
{
	__unwind_state_t* state = (__unwind_state_t*) arg;

	uintptr_t pc = _Unwind_GetIP(context);
	if (pc) {
		stackframe_t* frame = state->current++;
		if (frame == state->end) {
			return _URC_END_OF_STACK;
		} else {
			int status = __addr_info((void*) pc, &frame->module_base, &frame->symbol_addr);
			if (status != 0) {
				frame->module_base = 0;
				frame->symbol_addr = pc;
			}
		}
	}
	return _URC_NO_REASON;
}

int create_backtrace(stackframe_t* frames, int size) {
	MEMPROF_LOG("create_backtrace enter\n");
	__unwind_state_t state = {frames, frames + size};
	_Unwind_Backtrace(__unwind_callback, &state);

	int num_frames = state.current - frames;

	MEMPROF_LOG("create_backtrace exit: %d frames\n", num_frames);
	return num_frames;
}

#define MEMPROF_MAX_FRAMES 100
#define MEMPROF_MAX_MODULES 100
#define MEMPROF_SKIP_TOP_FRAMES 2

#if defined(__GNUC__)
	#define MEMPROF_ATOMIC_INT volatile int
	#define MEMPROF_ATOMIC_INC(a_ptr) __sync_fetch_and_add(a_ptr, 1)
#else
	#include <sys/atomics.h>
	#define MEMPROF_ATOMIC_INT volatile int
	#define MEMPROF_ATOMIC_INC(a_ptr) __atomic_inc(a_ptr)
#endif



#define MEMPROF_DESC_ALLOC 1
#define MEMPROF_DESC_FREE 2

static MEMPROF_ATOMIC_INT g_memprof_id;

static FILE* g_memprof_alloc_file;
static FILE* g_memprof_info_file;

const char* g_memprof_alloc_filename = "/data/local/tmp/memprof.alloc";
const char* g_memprof_info_filename = "/data/local/tmp/memprof.info";


static uintptr_t g_memprof_known_modules[MEMPROF_MAX_MODULES];

static uintptr_t* find_known_module(uintptr_t module) {
	for (int i = 0; i < MEMPROF_MAX_MODULES; ++i) {
		uintptr_t* current = g_memprof_known_modules + i;

		if (*current == 0 || *current == module) {
			return current;
		}
	}

	assert(0 && "Exceed MEMPROF_MAX_MODULES");
	return NULL;
}

static void maybe_log_modules(const alloc_desc_t* desc) {
	if (!g_memprof_info_file) {
		g_memprof_info_file = fopen(g_memprof_info_filename, "w+b");
	}

	for (int i = 0; i < desc->num_frames; ++i) {
		uintptr_t module = desc->frames[i].module_base;
		uintptr_t* known = find_known_module(module);

		if (*known == module) {
			continue;
		}

		*known = module;

		module_info_t info = {0};
		int status = create_module_info(&info, module);
		if (status != 0) {
      MEMPROF_LOG("unresolved module %lx\n", module);
			return; // leave module unresolved
		}

		status = write_module_info(&info, g_memprof_info_file);
		if (status != 0) {
			assert(0 && "write_module_info failed");
		}
	}
}

void memprof_log(const alloc_desc_t* desc) {
	if (!g_memprof_alloc_file) {
		g_memprof_alloc_file = fopen(g_memprof_alloc_filename, "w+b");
	}

	int status = write_alloc_desc(desc, g_memprof_alloc_file);
	if (status != 0) {
		assert(0 && "write_alloc_desc failed");
	}
}

void log_mem_alloc(const void* mem, size_t size) {
	stackframe_t frames[MEMPROF_MAX_FRAMES];

	int num_frames = create_backtrace(frames, MEMPROF_MAX_FRAMES);
	if (num_frames < 0) {
      assert(0 && "unable to get backtrace");
	}

	alloc_desc_t desc = {0};

	// desc.id = atomic_fetch_add(&g_mem_prof_id, 1);
	desc.id = MEMPROF_ATOMIC_INC(&g_memprof_id);
	desc.type = MEMPROF_DESC_ALLOC;
	desc.timestamp = (int32_t) time(NULL);
	desc.memptr = (uintptr_t) mem;
	desc.size = size;

	desc.num_frames = num_frames - MEMPROF_SKIP_TOP_FRAMES;
	desc.frames = frames + MEMPROF_SKIP_TOP_FRAMES;

	memprof_log(&desc);
}

void log_mem_free(const void* mem) {
	stackframe_t frames[MEMPROF_MAX_FRAMES];

	int num_frames = create_backtrace(frames, MEMPROF_MAX_FRAMES);
	if (num_frames < 0) {
		assert(0 && "unable to get backtrace");
	}

	alloc_desc_t desc = {0};

	// desc.id = atomic_fetch_add(&g_mem_prof_id, 1);
	desc.id = MEMPROF_ATOMIC_INC(&g_memprof_id);
	desc.type = MEMPROF_DESC_FREE;
	desc.memptr = (uintptr_t) mem;
	desc.size = 0;

	desc.num_frames = num_frames - MEMPROF_SKIP_TOP_FRAMES;
	desc.frames = frames + MEMPROF_SKIP_TOP_FRAMES;

	memprof_log(&desc);
}

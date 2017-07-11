#ifndef TGEN_CONFIG_H
#define TGEN_CONFIG_H

#include <stdint.h>

#if defined(_M_X64) || defined(__amd64__)
#define IS_X64
#endif

static const uint32_t IMAGE_BASE = 0x400000;
static const uint32_t SQLITE_TABLE = 0x56A290;
static const uint32_t STATIC_START = 0x558408;
static const uint32_t STATIC_END = 0x558548;
static const uint32_t SERVER_ENTRYPOINT = 0x549C50;
static const uint32_t SERVER_ENTRYPOINT_END = 0x549F9D;

static const uint32_t VA_CREATE_STRING_FROM_CSTR = 0x401A40;
static const uint32_t VA_GENERATOR = 0x518630;
static const uint32_t VA_GET_SECTOR_CHUNK_DATA = 0x406290;

inline bool has_ignore_static(unsigned int x)
{
    // return x == 0x5566C0 || x == 0x5566D0 || x == 0x5566E0;
    return x == 0 || x == 1 || x == 2 || x == 6 || x == 7 || x == 8;
}

#endif // TGEN_CONFIG_H

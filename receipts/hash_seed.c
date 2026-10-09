/* Measurement-only macOS entropy control, mirroring sprint-det's seed/draw policy. */
#include <CommonCrypto/CommonRandom.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static _Thread_local uint64_t drawn;
static _Atomic uint64_t calls;

static uint64_t mix(uint64_t x) {
    uint64_t z = x + UINT64_C(0x9e3779b97f4a7c15);
    z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
    return z ^ (z >> 31);
}

static CCRNGStatus seeded_random(void *bytes, size_t count) {
    const char *value = getenv("RH_HASHSEED");
    if (!value || !*value) return CCRandomGenerateBytes(bytes, count);
    char *end;
    uint64_t seed = strtoull(value, &end, 10);
    if (*end) return CCRandomGenerateBytes(bytes, count);
    atomic_fetch_add(&calls, 1);
    unsigned char *out = bytes;
    for (size_t i = 0; i < count; ) {
        uint64_t word = mix(seed ^ mix(drawn++));
        for (int j = 0; j < 8 && i < count; j++, i++) {
            out[i] = (word >> (8 * j)) & 255;
        }
    }
    return kCCSuccess;
}

__attribute__((used, section("__DATA,__interpose")))
static const struct { const void *replacement; const void *original; } interpose = {
    (const void *)seeded_random, (const void *)CCRandomGenerateBytes
};

__attribute__((destructor))
static void receipt(void) {
    uint64_t n = atomic_load(&calls);
    if (n) fprintf(stderr, "rh-hashseed: {\"calls\":%llu}\n", (unsigned long long)n);
}

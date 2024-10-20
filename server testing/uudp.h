#include <time.h>

typedef struct {
    long long sequence;
    long long timestamp;
    const char *test_string = "Hello World";
} data_packet;

long long sequence = 1;
#ifndef _cft_STRING
#define _cft_STRING

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <io.h>

#define _cft_ENCODING_OLD _O_TEXT
#define _cft_ENCODING_BINARY _O_BINARY
#define _cft_ENCODING_WIN_U16 _O_WTEXT
#define _cft_ENCODING_U16 _O_U16TEXT
#define _cft_ENCODING_U8 _O_U8TEXT

#define _cft_ENCODING_DEFAULT _cft_ENCODING_U8

#define _cft_SET_OUTPUT_ENCODING(_cft_encoding) _setmode(_fileno(stdout), _cft_encoding)
#define _cft_INIT_OUTPUT _cft_SET_OUTPUT_ENCODING(_cft_ENCODING_DEFAULT)

#define _cft_string(_cft_value) L##_cft_value
#define _cft_printf(_cft_value, ...) wprintf(_cft_string(_cft_value), __VA_ARGS__)

#endif

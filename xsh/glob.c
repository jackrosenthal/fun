#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include <lithium/unit.h>

#include "macros.h"

#include "glob.h"

bool xsh_glob_match(const char *pattern, const char *str)
{
	if (!pattern[0])
		return !str[0];

	switch (pattern[0]) {
	case '?':
		if (!str[0])
			return false;
		return xsh_glob_match(pattern + 1, str + 1);
	case '*':
		if (str[0] && xsh_glob_match(pattern, str + 1))
			return true;
		return xsh_glob_match(pattern + 1, str);
	case '\\':
		/* Interpret the next character literally */
		if (!pattern[1])
			return false;
		pattern++;
		FALLTHROUGH;
	default:
		if (!str[0])
			return false;
		if (pattern[0] != str[0])
			return false;
		return xsh_glob_match(pattern + 1, str + 1);
	}
}

DEFTEST("xsh.glob.match_no_special_chars", {}) {
	EXPECT(xsh_glob_match("hello world", "hello world"));
	EXPECT(!xsh_glob_match("nothing special", "hello world"));
}

DEFTEST("xsh.glob.match_wild_char", {}) {
	EXPECT(xsh_glob_match("hello.???", "hello.com"));
	EXPECT(!xsh_glob_match("hello.???", "hello.sh"));
}

DEFTEST("xsh.glob.match_star", {}) {
	EXPECT(xsh_glob_match("hello.*", "hello.com"));
	EXPECT(xsh_glob_match("hello.*", "hello.sh"));
	EXPECT(xsh_glob_match("hello.*", "hello."));
	EXPECT(!xsh_glob_match("hello.*", "hello"));
	EXPECT(!xsh_glob_match("hello.*", "hello_world.exe"));
	EXPECT(xsh_glob_match("*.*", "hello.com"));
	EXPECT(xsh_glob_match("*.*", "."));
	EXPECT(!xsh_glob_match("*.*", "noperiod"));
	EXPECT(xsh_glob_match("*.*.*", ".."));
	EXPECT(!xsh_glob_match("*.*.*", "."));
}

DEFTEST("xsh.glob.escape", {}) {
	EXPECT(xsh_glob_match("hello\\*", "hello*"));
	EXPECT(!xsh_glob_match("hello\\*", "hello.exe"));
	EXPECT(!xsh_glob_match("hello\\", "hello"));
}

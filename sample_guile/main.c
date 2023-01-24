#include <stdio.h>

#include <libguile.h>

static SCM hello(SCM name)
{
	SCM output_port = scm_current_output_port();
	SCM format = scm_from_utf8_string("hello ~A~%");
	SCM args = scm_list_1(name);

	scm_simple_format(output_port, format, args);

	return SCM_EOL;
}

static void *func(void *data)
{
	scm_c_define("name", scm_from_utf8_string(data));
	scm_c_define_gsubr("hello", 1, 0, 0, hello);
	scm_c_eval_string("(hello name)");

	return NULL;
}

int main(int argc, char *argv[])
{
	scm_with_guile(func, argv[1] ? argv[1] : "world");
	return 0;
}

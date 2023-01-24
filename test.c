#include <stdio.h>

int main(int argc, char *argv[])
{
	char *example[] = {argv[0], NULL};

	printf("%s\n", example[0]);
	return 0;
}

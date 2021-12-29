#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define MAX_STUDENTS 15
#define MAX_PAIRS ((MAX_STUDENTS * (MAX_STUDENTS - 1)) / 2)

static int students;
static struct {
	int num_disallowed;
	int list[MAX_STUDENTS];
} requests[MAX_STUDENTS];
static int assignments[MAX_STUDENTS];

static bool ok(int group, int student)
{
	for (int i = 0; i < requests[student].num_disallowed; i++) {
		if (assignments[requests[student].list[i]] == group)
			return false;
	}

	return true;
}

static bool find_solution(int groups, int student_to_assign)
{
	/* Base case */
	if (student_to_assign >= students)
		return true;

	for (int group = 0; group < groups; group++) {
		if (!ok(group, student_to_assign))
			continue;

		assignments[student_to_assign] = group;

		if (find_solution(groups, student_to_assign + 1))
			return true;
	}

	assignments[student_to_assign] = -1;
	return false;
}

static int find_min_pairs(void)
{
	for (int groups = 1; groups <= students; groups++) {
		for (int i = 0; i < students; i++)
			assignments[i] = -1;

		if (find_solution(groups, 0))
			return groups;
	}

	return -1;
}

int main(void)
{
	int num_requests;

	scanf("%d\n", &students);
	scanf("%d\n", &num_requests);

	for (int i = 0; i < num_requests; i++) {
		int a;
		int b;

		scanf("%d %d\n", &a, &b);

		/* Adjust to zero index */
		a--;
		b--;

		requests[a].list[requests[a].num_disallowed++] = b;
		requests[b].list[requests[b].num_disallowed++] = a;
	}

	printf("%d\n", find_min_pairs());
	return 0;
}

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define MAX_STUDENTS 15
#define MAX_PAIRS ((MAX_STUDENTS * (MAX_STUDENTS - 1)) / 2)

static int students;
static int requests;
static struct {
	int a;
	int b;
} request_pairs[MAX_PAIRS];

static bool find_solution(int groups, int *assignments)
{
	int student_to_assign = -1;

	/* Check for contradicting requests */
	for (int i = 0; i < requests; i++) {
		int assign_a = assignments[request_pairs[i].a];
		int assign_b = assignments[request_pairs[i].b];

		if (assign_a == -1) {
			student_to_assign = request_pairs[i].a;
			continue;
		}

		if (assign_b == -1) {
			student_to_assign = request_pairs[i].b;
			continue;
		}

		if (assign_a == assign_b)
			return false;
	}

	/* All requests satisfied is the base case */
	if (student_to_assign == -1)
		return true;

	for (int group = 0; group < groups; group++) {
		assignments[student_to_assign] = group;

		if (find_solution(groups, assignments))
			return true;
	}

	assignments[student_to_assign] = -1;
	return false;
}

static int find_min_pairs(void)
{
	int assignments[MAX_STUDENTS];

	for (int groups = 1; groups <= students; groups++) {
		for (int i = 0; i < students; i++)
			assignments[i] = -1;

		if (find_solution(groups, assignments))
			return groups;
	}

	return -1;
}

int main(void)
{
	scanf("%d\n", &students);
	scanf("%d\n", &requests);

	for (int i = 0; i < requests; i++) {
		scanf("%d %d\n", &request_pairs[i].a, &request_pairs[i].b);

		/* Adjust to zero index */
		request_pairs[i].a -= 1;
		request_pairs[i].b -= 1;
	}

	printf("%d\n", find_min_pairs());
	return 0;
}

project('xsh', 'c')

lithium_dep = declare_dependency(link_args: '-lithium')
deps = [lithium_dep]

libxsh_src = files('glob.c')

run_tests = executable(
    'run_tests',
    libxsh_src + ['run_tests.c'],
    c_args: ['-DLITHIUM_TEST_BUILD'],
    dependencies: deps,
)
test('run_tests', run_tests)

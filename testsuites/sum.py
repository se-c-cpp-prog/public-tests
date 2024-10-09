import os

import testsuites.base as base

from typing import Iterable, Tuple, List

TEST_DATA_DIR = 'testdata'
SUM_DIR = os.path.join(TEST_DATA_DIR, 'sum')

def test_naming(a: int, b: int, is_file: bool = True) -> str:
	if is_file:
		return "test_%d_%d" % (a, b)
	return "%d + %d" % (a, b)

def file_naming(a: int, b: int, suffix: str) -> str:
	return "%s.%s" % (test_naming(a, b), suffix)

def file_dir_naming(a: int, b: int, suffix: str) -> str:
	basename = file_naming(a, b, suffix)
	return os.path.join(SUM_DIR, basename)

def generate_tests() -> Iterable[Tuple[str, List[str], str, str]]:
	paths = [TEST_DATA_DIR, SUM_DIR]

	for p in paths:
		if os.path.exists(p) and not os.path.isdir(p):
			raise ValueError("[FATAL ERROR] Provided path \"%s\" should be directory." % (p))

		if not os.path.exists(p):
			os.mkdir(p)

	generated: Iterable[Tuple[str, str, str]] = []

	for a in range(1, 10):
		for b in range(10, 20):
			name = test_naming(a, b, False)
			raw_input = file_dir_naming(a, b, 'in')
			raw_output = file_dir_naming(a, b, 'out')
			raw_expected = file_dir_naming(a, b, 'ref')
			with open(raw_input, 'w') as stream:
				stream.write("%d %d\n" % (a, b))
			with open(raw_expected, 'w') as stream:
				stream.write("%d\n" % (a + b))
			test_data = (name, [raw_input, raw_output], raw_output, raw_expected)
			generated.append(test_data)

	return generated

def get_instance() -> base.BaseTester:
	hello_tester = base.BaseTester(is_stdin_input = False, is_raw_input = True, is_raw_output = False)

	tests = generate_tests()

	for test_data in tests:
		test_name, test_input, test_output_stream, test_expected = test_data
		hello_tester.add_success(test_name, test_input, test_expected, test_output_stream)

	return hello_tester

import testsuites.base as base

from typing import Tuple, Optional, Dict, Iterable, List

SUITE_NAME = "expression"

__ALL_GOOD_CATEGORIES = ["nop", "unary plus", "unary minus",
						 "addition", "subtraction",
						 "power", "product", "division", "remainder",
						 "bitwise NOT", "bitwise AND", "bitwise OR", "bitwise XOR", "bitwise left shift", "bitwise right shift", "(complex)"]
__ALL_BAD_CATEGORIES = ["binary (neg)", "binary (UB/ID)", "(complex) (neg)"]

__ALL_CATEGORIES = __ALL_GOOD_CATEGORIES + __ALL_BAD_CATEGORIES

class __GoodComparator(base.BaseComparator):
	def __init__(self):
		super().__init__()

	def compare(self, actual: List[str], expected: List[str]) -> base.BaseResult:
		# Check number of lines.
		if len(actual) != len(expected):
			return base.err_assertion_len(len(actual), len(expected))

		# Remove empty (newline) element.
		actual.pop()
		expected.pop()

		# Comparison.
		out = actual[0]
		ref = expected[0]

		if out != ref:
			return base.BaseResult(base.Errno.ERROR_ASSERTION, what = "expected \"%s\", but found \"%s\"" % (ref, out))

		return base.err_ok()

class __TestData:
	def __init__(self, input_expr: str, expected: str, returncode: int = 0):
		self.__expression = input_expr
		self.__expected = expected
		self.__returncode = returncode

	def get_input(self) -> str:
		return self.__expression

	def get_expected(self) -> str:
		return self.__expected
		
	def get_returncode(self) -> str:
		return self.__returncode

	def is_failed(self) -> bool:
		return self.__expected == None

def __generate_bad_categorized_tests(category: str, tests: List[str]) -> List[Tuple[str, str, __TestData]]:
	cat_generated: List[Tuple[str, str, __TestData]] = []
	for i, t in enumerate(tests):
		test =__TestData(t[0], "", t[1])
		test_data = (f"{category} #{i}: '{test.get_input()}'", category, test.get_returncode(), test)
		cat_generated.append(test_data)
	return cat_generated

def __generate_bad_tests() -> Iterable[Tuple[str, str, __TestData]]:
	generated: List[Tuple[str, str, __TestData]] = []

	E_SUPPORT = 1
	E_MATH = 2
	E_PARSER = 3

	tests = [
		["* 2", E_PARSER], ["2 *", E_PARSER],
		["/ 2", E_PARSER], ["2 /", E_PARSER],
		["% 2", E_PARSER], ["2 %", E_PARSER],
		["& 2", E_PARSER], ["2 &", E_PARSER],
		["| 2", E_PARSER], ["2 |", E_PARSER],
		["^ 2", E_PARSER], ["2 ^", E_PARSER],
		["<< 2", E_PARSER], ["2 >>", E_PARSER],
		[">> 2", E_PARSER], ["2 >>", E_PARSER],
		["2 * * 2", E_PARSER], ["2 * 2 *", E_PARSER], [" * 2 ** 2", E_PARSER]
	]
	generated += __generate_bad_categorized_tests('binary (neg)', tests)
		
	tests = [
		["2 ** -2", E_MATH],
		["0 / 0", E_MATH], ["-2147483648 / -1", E_MATH],
		["0 % 0", E_MATH], ["-2147483648 % -1", E_MATH],
		["1 << 32", E_MATH], ["1 << 60", E_MATH], ["1 << -1", E_MATH],
		["1 >> 32", E_MATH], ["1 >> 60", E_MATH], ["1 >> -1", E_MATH]
	]
	generated += __generate_bad_categorized_tests('binary (UB/ID)', tests)

	tests = [
		["( 22 - 5 ) + 556 * ( 2 + 2", E_PARSER],
		["( ( 22 - 5 ) + 556 * ( 2 + 2 )", E_PARSER],
		["( ( 22 - 5 ) + ( 556 * ( 2 + 2 ) )", E_PARSER],
		["( 22 - 5 ) + 556 * ( 2 + 2 ) )", E_PARSER],
		["( 22 - 5 ) + 556 ) * ( 2 + 2 )", E_PARSER],

		["()", E_PARSER], ["(", E_PARSER], [")", E_PARSER],
		["+", E_PARSER], ["=", E_SUPPORT], ["\\", E_SUPPORT],
		["2***2", E_PARSER], ["2+++2", E_PARSER], ["2+-+2", E_PARSER],
		["4* 8", E_PARSER], ["4 +8", E_PARSER], ["4 ~8", E_PARSER],

		["1 + ( 2 * * 2 )", E_PARSER],
		["( 2 * 2 * ) + 6", E_PARSER],
		["9 + ( * 2 ** 2 )", E_PARSER],
	]
	generated += __generate_bad_categorized_tests('(complex) (neg)', tests)

	return generated

def __generate_good_categorized_tests(category: str, tests: List[str]) -> List[Tuple[str, str, __TestData]]:
	cat_generated: List[Tuple[str, str, __TestData]] = []
	for i, t in enumerate(tests):
		test =__TestData(t[0], t[1])
		test_data = (f"{category} #{i}: '{test.get_input()}' -> '{test.get_expected()}'", category, test)
		cat_generated.append(test_data)
	return cat_generated

def __generate_good_tests() -> Iterable[Tuple[str, str, __TestData]]:
	generated: List[Tuple[str, str, __TestData]] = []

	tests = [
		["0", "0"],
		["1", "1"],
		["2147483647", "2147483647"]
	]
	generated += __generate_good_categorized_tests('nop', tests)

	tests = [
		["+ 0", "0"],
		["+ 1", "1"],
		["+1", "1"],
		["+2147483647", "2147483647"]
	]
	generated += __generate_good_categorized_tests('unary plus', tests)

	tests = [
		["- 0", "0"],
		["- 1", "-1"],
		["-1", "-1"],
		["-2147483647", "-2147483647"]
	]
	generated += __generate_good_categorized_tests('unary minus', tests)

	tests = [
		["0 + 0", "0"],
		["0 + 1", "1"],
		["10 + 1", "11"],
		["-2147483648 + 1", "-2147483647"],
		["2147483647 + 1", "-2147483648"],
		["225 + 526", "751"]
	]
	generated += __generate_good_categorized_tests('addition', tests)

	tests = [
		["0 - 0", "0"],
		["0 - 1", "-1"],
		["10 - 1", "9"],
		["-2147483648 - 1", "2147483647"],
		["2147483647 - 1", "2147483646"],
		["225 - 526", "-301"]
	]
	generated += __generate_good_categorized_tests('subtraction', tests)
	
	tests = [
		["0 ** 0", "1"],
		["0 ** 1", "0"],
		["1 ** 1", "1"],
		["-1 ** 2", "-1"],
		["-1 ** 3", "-1"],
		["10 ** 8", "100000000"],
		["10 ** 10", "1410065408"],
		["10 ** 40", "0"],
		["-2147483648 ** 1", "-2147483648"],
		["2147483647 ** 1", "2147483647"]
	]
	generated += __generate_good_categorized_tests('power', tests)
	
	tests = [
		["0 * 0", "0"],
		["0 * 1", "0"],
		["1 * 1", "1"],
		["10 * 100", "1000"],
		["-2147483648 * 1", "-2147483648"],
		["2147483647 * 1", "2147483647"],
		["225 * 526", "118350"]
	]
	generated += __generate_good_categorized_tests('product', tests)
	
	tests = [
		["0 / 1", "0"],
		["1 / 1", "1"],
		["10 / 100", "0"],
		["2147483647 / 1", "2147483647"],
		["526 / 225", "2"],
		["7 / 2", "3"],
		["17 / 5", "3"],
		["17 / -5", "-3"],
		["-17 / 5", "-3"],
		["-17 / -5", "3"]
	]
	generated += __generate_good_categorized_tests('division', tests)
	
	tests = [
		["0 % 1", "0"],
		["1 % 1", "0"],
		["10 % 100", "10"],
		["526 % 225", "76"],
		["7 % 2", "1"],
		["17 % 5", "2"],
		["17 % -5", "2"],
		["-17 % 5", "-2"],
		["-17 % -5", "-2"]
	]
	generated += __generate_good_categorized_tests('remainder', tests)
	
	tests = [
		["~0", "-1"],
		["~ 1", "-2"],
		["~1", "-2"],
		["~2147483647", "-2147483648"],
		["~225", "-226"],
		["~-2147483647", "2147483646"]
	]
	generated += __generate_good_categorized_tests('bitwise NOT', tests)
	
	tests = [
		["0 & 225", "0"],
		["15 & 6", "6"],
		["2730 & 990", "650"],
		["2147483647 & 1", "1"],
		["2147483646 & 1", "0"],
		["2147483647 & 2147483647", "2147483647"],
		["2147483647 & -2147483647", "1"],
		["-1 & 2730", "2730"]
	]
	generated += __generate_good_categorized_tests('bitwise AND', tests)
	
	tests = [
		["0 | 225", "225"],
		["15 | 6", "15"],
		["2730 | 990", "3070"],
		["2147483647 | 4", "2147483647"],
		["1 | 1", "1"],
		["2147483647 | -2147483647", "-1"]
	]
	generated += __generate_good_categorized_tests('bitwise OR', tests)
	
	tests = [
		["0 ^ 225", "225"],
		["15 ^ 6", "9"],
		["2730 ^ 990", "2420"],
		["2147483647 ^ 4", "2147483643"],
		["1 ^ 1", "0"],
		["2147483647 ^ -2147483647", "-2"]
	]
	generated += __generate_good_categorized_tests('bitwise XOR', tests)
	
	tests = [
		["0 << 1", "0"],
		["15 << 2", "60"],
		["2730 << 9", "1397760"],
		["2147483647 << 0", "2147483647"],
		["1 << 31", "-2147483648"]
	]
	generated += __generate_good_categorized_tests('bitwise left shift', tests)
	
	tests = [
		["0 >> 1", "0"],
		["15 >> 2", "3"],
		["2730 >> 5", "85"],
		["2147483647 >> 30", "1"],
		["1 >> 31", "0"]
	]
	generated += __generate_good_categorized_tests('bitwise right shift', tests)
	
	tests = [
		["( 225526 )", "225526"],
		["( -1 ) ** 2", "1"],
		["( -1 ) ** 3", "-1"],
		["2 + ( 3 + 5 )", "10"],
		["10 + ( 7 - ( ~8 ) )", "26"],

		["5 - +7", "-2"],
		["5 + + +7", "12"],
		["5 + ++7", "12"],

		["5 - - -7", "-2"],
		["5 - --7", "-2"],
		["5 - - ( -7 )", "-2"],

		["5 * ( 4 - ( 5 + 2 ) * 4 )", "-120"],
		["2 * 3 ** 4", "162"],
		["2 * 3 ** 4 + 1", "163"],

		["(2 * 3) ** 4", "1296"],
		["(2 * 3) ** 4 + 1", "1297"],

		["( 1 + ( 1 + ( 2 + 1 ) ) )", "5"],
		["1 / ( 1 + ( 2 + 3 ) )", "0"],
		["1 / 1 + ( 2 + 3 )", "6"],

		["55 / ( 55 - 54 ) / 10", "5"],
		["42 - ( 42 + 89 ) - 89 + 56 - ( 56 )", "-178"],

		["5 + ( 6 - 2 ) * 9 + 3 ^ ( 7 - 1 )", "42"],

		["( 2 ** 1 ) + +5 / 1 - -2 + 6 * ( 7 >> 2 ) % 4 << ( 4 | 8 ^ 7 | ~ ( -2 & ~ 6 ) )", "360448"],
		["( ( 2 ** 1 ) + +5 / 1 - -2 + 6 * ( 7 >> 2 ) % 4 ) << ( 4 | 8 ^ 7 | ~ ( -2 & ~ 6 ) )", "360448"],

		["2 + 3 + 2 + 5 + 8 + 9 + 4 + 7 + 5 + 4 + 1 + 4 + 8 + 4 + 4 + 7 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 5 + 5 + 2 + 21 + 85 + 98 + 4 + 1 + 64 + 8451 + 484 + 1 + 94 + 8 + 4 + 51 + 84 + 1", "9568"],
		["( 2 + ( 3 + 2 + ( 5 + 8 + ( 9 + 4 + 7 + 5 + 4 + 1 ) + 4 + 8 + ( 4 + 4 + 7 + 4 + 4 ) + 4 + 4 + ( 4 + 4 + 4 + 5 + 5 ) + 2 + ( 21 + 85 + 98 + 4 + 1 + 64 ) + 8451 + 484 + 1 ) + 94 + 8 ) + 4 + 51 + 84 ) + 1", "9568"],
		["( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( 2 + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2 ) + 2", "204"],
	]
	generated += __generate_good_categorized_tests('(complex)', tests)

	return generated

def get_instance() -> Tuple[base.BaseTester, Optional[Dict[str, float]]]:
	TIMEOUT = 1.5

	expression_tester = base.BaseTester(is_stdin_input = False, is_raw_input = True, is_raw_output = True)

	good_tests = __generate_good_tests()
	bad_tests = __generate_bad_tests()
	coefficients = base.get_coefficients(SUITE_NAME, __ALL_CATEGORIES)
	good_comparator = __GoodComparator()

	for test_data in good_tests:
		test_name, test_category, test = test_data
		expression_tester.add_success(test_name, test.get_input(), test.get_expected(), timeout = TIMEOUT, categories = [test_category], comparator = good_comparator)

	for test_data in bad_tests:
		test_name, test_category, test_exitcode, test = test_data
		expression_tester.add_failed(test_name, test.get_input(), test_exitcode, timeout = TIMEOUT, categories = [test_category])

	return expression_tester, coefficients

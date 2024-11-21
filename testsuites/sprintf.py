import testsuites.base as base

from typing import Tuple, Optional, Dict, Iterable, List

SUITE_NAME = 'sprintf'

__ALL_GOOD_CATEGORIES = ['16to10', '8to10', '2to10', '10to16', '8to16', '2to16', '16to10 extended', 'XtoX', 'HUGEXto10', 'HUGE10toX']
__ALL_BAD_CATEGORIES = ['neg']

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
	def __init__(self, format: str, number: str, expected: Optional[str] = None):
		self.__format = format
		self.__number = number
		self.__expected = expected

	def get_input(self) -> List[str]:
		return [self.__format, self.__number]

	def get_expected(self) -> str:
		return self.__expected

	def is_failed(self) -> bool:
		return self.__expected == None

def __generate_answer(fmt: str, value_str: str):
	value_sign = value_str[0] == "-"

	if value_sign:
		value_str = value_str[1:]

	base = 2 if value_str[0:2] == "0b" else 16 if value_str[0:2] == "0x" or value_str[0:2] == "0X" else 8 if value_str[0:1] == "0" else 10
	value = int(value_str, base = base)

	if value_sign:
		value = -value
	try:
		res = f"{fmt % (value)}"
	except Exception as ex:
		formatter = lambda x: format(x, fmt[1:])
		res = formatter(value)
	return res

def __create_test(fmt: str, input_value: str, out_value: Optional[str] = None) -> __TestData:
	value_str = input_value
	input_value_str = value_str.replace("0o", "0")
	ref_value_str = out_value if out_value != None else f"{__generate_answer(fmt, input_value)}".replace("0o", "0")
	return __TestData(fmt, input_value_str, ref_value_str)

def __generate_bad_tests() -> Iterable[Tuple[str, str, int, __TestData]]:
	generated: List[Tuple[str, str, int, __TestData]] = []

	category = 'neg'
	tests = [
		["", ""],
		["d", "0"],
		["%", "0"],
		["%f", "0"],
		["%i", "0"],
		["%d", "12ABC"]
	]

	for i, t in enumerate(tests):
		test = __TestData(t[0], t[1])
		test_data = (f"Bad situation #{i}: \"{'\" \"'.join(test.get_input())}\"", category, 1, test) # TODO: Double check returncode for all bad situations.
		generated.append(test_data)

	return generated

def __generate_good_tests() -> Iterable[Tuple[str, str, __TestData]]:
	generated: List[Tuple[str, str, __TestData]] = []

	uint32_t_values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 25, 34, 63, 64, 85, 99, 100, 127, 128, 196, 2**30, 2**31 - 1, 2**31, -2**31, 2**32 - 1, 2**32, 2**63 - 1, 2**63, -2**63, 2**64 - 1, 2**64]

	formats_values = ["", "1", "2", "3", "5", " ", " 1", " 2", " 3", " 5", "+", "+1", "+2", "+3", "+5", "0", "-", "-1", "-2", "-3", "-5"]
	formats2_values = ["+ 7", " +7", "+ 07", " +07", "+0 7", "0+ 7", "0 +7", " 0+7", "-+ 7", "+- 7", " +-7", " -+7"]

	category = '16to10'
	for i, t in enumerate([["%d", f"{hex(i)}"] for i in uint32_t_values]):
		test =__create_test(t[0], t[1])
		test_data = (f"{category} #{i}: \"{'\" \"'.join(test.get_input())}\" -> '{test.get_expected()}'", category, test)
		generated.append(test_data)

	category = '8to10'
	for i, t in enumerate([["%d", f"{oct(i)}"] for i in uint32_t_values]):
		test =__create_test(t[0], t[1])
		test_data = (f"{category} #{i}: \"{'\" \"'.join(test.get_input())}\" -> '{test.get_expected()}'", category, test)
		generated.append(test_data)

	category = '2to10'
	for i, t in enumerate([["%d", f"{bin(i)}"] for i in uint32_t_values]):
		test =__create_test(t[0], t[1])
		test_data = (f"{category} #{i}: \"{'\" \"'.join(test.get_input())}\" -> '{test.get_expected()}'", category, test)
		generated.append(test_data)

	category = '10to16'
	for i, t in enumerate([["%x", f"{int(i)}"] for i in uint32_t_values]):
		test =__create_test(t[0], t[1])
		test_data = (f"{category} #{i}: \"{'\" \"'.join(test.get_input())}\" -> '{test.get_expected()}'", category, test)
		generated.append(test_data)

	category = '8to16'
	for i, t in enumerate([["%x", f"{oct(i)}"] for i in uint32_t_values]):
		test =__create_test(t[0], t[1])
		test_data = (f"{category} #{i}: \"{'\" \"'.join(test.get_input())}\" -> '{test.get_expected()}'", category, test)
		generated.append(test_data)

	category = '2to16'
	for i, t in enumerate([["%x", f"{bin(i)}"] for i in uint32_t_values]):
		test =__create_test(t[0], t[1])
		test_data = (f"{category} #{i}: \"{'\" \"'.join(test.get_input())}\" -> '{test.get_expected()}'", category, test)
		generated.append(test_data)

	category = '16to10 extended'
	tests = [[f"%{fmt}d", "0x0"] for fmt in formats_values] \
		+ [[f"%{fmt}d", "-0x0"] for fmt in formats_values] \
		+ [[f"%{fmt}d", "0x1"] for fmt in formats_values] \
		+ [[f"%{fmt}d", "-0x1"] for fmt in formats_values] \
		+ [[f"%{fmt}d", "0x22"] for fmt in formats_values] \
		+ [[f"%{fmt}d", "-0x55"] for fmt in formats_values] \
		+ [[f"%{fmt}d", "0x26"] for fmt in formats2_values] \
		+ [[f"%{fmt}d", "-0x26"] for fmt in formats2_values] \
		+ [[f"%{fmt}d", "0x225526"] for fmt in [" 50", "050"]]
	for i, t in enumerate(tests):
		test =__create_test(t[0], t[1])
		test_data = (f"{category} #{i}: \"{'\" \"'.join(test.get_input())}\" -> '{test.get_expected()}'", category, test)
		generated.append(test_data)

	category = 'XtoX'
	tests = [
		["%x", "0x10"], ["%-x", "0x10"], ["%-x",  "-0x10"], ["%+x",   "0x10"], ["%#x",   "0x10"], ["%#X",   "0x10"],
		["%d", "10"],   ["%-d", "10"],   ["%-d",  "-10"],   ["%+d",   "10"],
		["%o", "010"],  ["%-o", "010"],  ["%-o",  "-010"],  ["%+o",   "010"],
		["%b", "0b10"], ["%-b", "0b10"], ["%-b",  "-0b10"], ["%+b",   "0b10"]
	]
	for i, t in enumerate(tests):
		test =__create_test(t[0], t[1])
		test_data = (f"{category} #{i}: \"{'\" \"'.join(test.get_input())}\" -> '{test.get_expected()}'", category, test)
		generated.append(test_data)

	category = 'HUGEXto10'
	tests = [
		["%d", "0x8Ee4fACF834B20a0b0DE134F630E7342", "-150343060792470555638386732992063179966"], 
		["%d", "0x711B05307CB4DF5F4F21ECB09CF18CBE", "150343060792470555638386732992063179966"],
		["%d", "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", "-1"],
		["%d", "0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", "170141183460469231731687303715884105727"],
		["%d", "0x80000000000000000000000000000000", "-170141183460469231731687303715884105728"],
		["%d", "0x00000000000000000000000000000000", "0"],
		["%d", "-0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", "1"],
		["%d", "-0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", "-170141183460469231731687303715884105727"],
		["%d", "-0x80000000000000000000000000000000", "-170141183460469231731687303715884105728"],
		["%d", "-0x00000000000000000000000000000000", "0"],
		["%d", "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0", "-16"],
		["%d", "-0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0", "16"],
		["%d", "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0F", "-241"],
		["%d", "-0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0F", "241"],
		["%d", "0x1234567890ABCDEFabcdef123456789", "1512366075009453296252344423395190665"],
		["%d", "-0x1234567890ABCDEFabcdef123456789", "-1512366075009453296252344423395190665"],
		["%d", "0x4b3b4ca85a86c47a098a224000000000", "100000000000000000000000000000000000000"],
		["%d", "0x4b3b4ca85a86c47a098a223fffffffff", "99999999999999999999999999999999999999"],
		
		["%d", "02167117531740645440501303360464754303471502", "-150343060792470555638386732992063179966"], 
		["%d", "01610660246037132337276474417313023474306276", "150343060792470555638386732992063179966"],
		["%d", "03777777777777777777777777777777777777777777", "-1"],
		["%d", "01777777777777777777777777777777777777777777", "170141183460469231731687303715884105727"],
		["%d", "02000000000000000000000000000000000000000000", "-170141183460469231731687303715884105728"],
		["%d", "000000000000000000000000000000000", "0"],
		["%d", "-03777777777777777777777777777777777777777777", "1"],
		["%d", "-01777777777777777777777777777777777777777777", "-170141183460469231731687303715884105727"],
		["%d", "-02000000000000000000000000000000000000000000", "-170141183460469231731687303715884105728"],
		["%d", "-000000000000000000000000000000000", "0"],
		["%d", "03777777777777777777777777777777777777777760", "-16"],
		["%d", "-03777777777777777777777777777777777777777760", "16"],
		["%d", "03777777777777777777777777777777777777777417", "-241"],
		["%d", "-03777777777777777777777777777777777777777417", "241"],
		["%d", "011064254742205274675752746757044321263611", "1512366075009453296252344423395190665"],
		["%d", "-011064254742205274675752746757044321263611", "-1512366075009453296252344423395190665"],
		["%d", "01131664625026503304364046121044000000000000", "100000000000000000000000000000000000000"],
		["%d", "01131664625026503304364046121043777777777777", "99999999999999999999999999999999999999"],
		
		["%d", "0b10001110111001001111101011001111100000110100101100100000101000001011000011011110000100110100111101100011000011100111001101000010",  "-150343060792470555638386732992063179966"], 
		["%d", "0b1110001000110110000010100110000011111001011010011011111010111110100111100100001111011001011000010011100111100011000110010111110",  "150343060792470555638386732992063179966"],
		["%d", "0b11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111", "-1"],
		["%d", "0b01111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111",  "170141183460469231731687303715884105727"],
		["%d", "0b10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  "-170141183460469231731687303715884105728"],
		["%d", "0b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", "0"],
		["%d", "-0b11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111", "1"],
		["%d", "-0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111",  "-170141183460469231731687303715884105727"],
		["%d", "-0b10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  "-170141183460469231731687303715884105728"],
		["%d", "-0b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", "0"],
		["%d", "0b11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111110000", "-16"],
		["%d", "-0b11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111110000", "16"],
		["%d", "0b11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111100001111", "-241"],
		["%d", "-0b11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111100001111", "241"],
		["%d", "0b1001000110100010101100111100010010000101010111100110111101111101010111100110111101111000100100011010001010110011110001001",  "1512366075009453296252344423395190665"],
		["%d", "-0b1001000110100010101100111100010010000101010111100110111101111101010111100110111101111000100100011010001010110011110001001",  "-1512366075009453296252344423395190665"],
		["%d", "0b1001011001110110100110010101000010110101000011011000100011110100000100110001010001000100100000000000000000000000000000000000000",  "100000000000000000000000000000000000000"],
		["%d", "0b1001011001110110100110010101000010110101000011011000100011110100000100110001010001000100011111111111111111111111111111111111111", "99999999999999999999999999999999999999"],
	]
	for i, t in enumerate(tests):
		test =__create_test(t[0], t[1], t[2])
		test_data = (f"{category} #{i}: \"{'\" \"'.join(test.get_input())}\" -> '{test.get_expected()}'", category, test)
		generated.append(test_data)
		
	category = 'HUGE10toX'
	tests = [
		["%#X", "150343060792470555638386732992063179966", "0X711B05307CB4DF5F4F21ECB09CF18CBE"], 
		["%#X", "-150343060792470555638386732992063179966", "-0X711B05307CB4DF5F4F21ECB09CF18CBE"],
		["%#x", "21267647932558653966460912964485513216", "0x10000000000000000000000000000000"],
		["%#X", "170141183460469231731687303715884105727", "0X7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"],
		
		["%#o", "150343060792470555638386732992063179966", "01610660246037132337276474417313023474306276"], 
		["%#o", "-150343060792470555638386732992063179966", "-01610660246037132337276474417313023474306276"],

		["%#b", "150343060792470555638386732992063179966", "0b1110001000110110000010100110000011111001011010011011111010111110100111100100001111011001011000010011100111100011000110010111110"], 
		["%#b", "-150343060792470555638386732992063179966", "-0b1110001000110110000010100110000011111001011010011011111010111110100111100100001111011001011000010011100111100011000110010111110"],
	]
	for i, t in enumerate(tests):
		test =__create_test(t[0], t[1], t[2])
		test_data = (f"{category} #{i}: \"{'\" \"'.join(test.get_input())}\" -> '{test.get_expected()}'", category, test)
		generated.append(test_data)

	return generated

def get_instance() -> Tuple[base.BaseTester, Optional[Dict[str, float]]]:
	TIMEOUT = 0.5

	sprintf_tester = base.BaseTester(is_stdin_input = False, is_raw_input = True, is_raw_output = True)

	good_tests = __generate_good_tests()
	bad_tests = __generate_bad_tests()
	coefficients = base.get_coefficients(SUITE_NAME, __ALL_CATEGORIES)
	good_comparator = __GoodComparator()


	for test_data in good_tests:
		test_name, test_category, test = test_data
		sprintf_tester.add_success(test_name, test.get_input(), test.get_expected(), timeout = TIMEOUT, categories = [test_category], comparator = good_comparator)

	for test_data in bad_tests:
		test_name, test_category, test_exitcode, test = test_data
		sprintf_tester.add_failed(test_name, test.get_input(), test_exitcode, timeout = TIMEOUT, categories = [test_category])

	return sprintf_tester, coefficients

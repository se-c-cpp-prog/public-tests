import os
import subprocess
import time
import wget
import zipfile
import tarfile
import sys

from enum import Enum
from typing import List, Union, Tuple, Optional, Dict, Iterable, Set, Callable

TESTDATA_DIR = 'testdata'

class Errno(Enum):
	ERROR_SUCCESS = 'ok'
	ERROR_SHOULD_PASS = 'program should not fail'
	ERROR_SHOULD_FAIL = 'program should not return successful exitcode'
	ERROR_STDERR_EMPTY = 'standard error output is empty'
	ERROR_STDOUT_NOT_EMPTY = 'on error program should not writing anything to standard output'
	ERROR_STDERR_NOT_EMPTY = 'on successful program should not writing anything to standard error output'
	ERROR_EXITCODE = 'program returns wrong exitcode'
	ERROR_ASSERTION = 'assertion'
	ERROR_TIMEOUT = 'timeout expired'
	ERROR_FILE_NOT_FOUND = 'file not found'
	ERROR_FILE_CREATED_ON_ERROR = 'file was created (as empty or with undefined state) after failing'
	ERROR_FILE_RECREATED_ON_ERROR = 'file was recreated (as empty or with undefined state) after failing'
	ERROR_TYPE_ERROR = 'type casting error'
	ERROR_NO_NEWLINE = 'no newline at EOF'
	ERROR_UNKNOWN = 'unknown'

class BaseTestingType(Enum):
	T_TEXT = "text",
	T_BINARY = "bytes",
	T_META = "meta"

class BaseResult:
	def __init__(self, errno: Errno, exitcode: int = 0, timer: int = 1, output: Union[str, bytes] = '<no output>', stderr: str = '<no error output>', what: Optional[str] = None, testing_type: BaseTestingType = BaseTestingType.T_TEXT):
		self.__errno = errno
		self.__what = what

		self.output = output
		self.stderr = stderr

		self.exitcode = exitcode
		self.timer = timer

		self.testing_type = testing_type

	def get_verdict(self) -> str:
		return self.__errno.value

	def get_additional_info(self) -> Optional[str]:
		return self.__what

	def __str__(self) -> str:
		if self.__what is None:
			return "   Verdict: %s." % (self.__errno.value)
		else:
			return "   Verdict: %s.\n   Additional information: %s." % (self.__errno.value, self.__what)

	def ok(self) -> bool:
		return self.__errno == Errno.ERROR_SUCCESS

def is_windows() -> bool:
	return sys.platform.startswith('win32')

def suite_to_dirname(suite: str) -> str:
	# All directories should have `_` instead of `-`.
	return suite.replace('-', '_')

def ensure_existence_directory(dirname: str):
	# Check if it's exists, otherwise create parent.
	if not os.path.exists(dirname):
		ensure_existence_directory(os.path.abspath(os.path.join(dirname, os.pardir)))

	# Check if it is directory, otherwise - it's fatal error.
	if os.path.exists(dirname) and os.path.isfile(dirname):
		raise ValueError("[FATAL ERROR] Provided path \"%s\" should be directory." % (os.path.abspath(dirname)))

	# Create directory.
	if not os.path.exists(dirname):
		os.mkdir(dirname)

def make_suite_dirname(suite: str) -> str:
	ensure_existence_directory(TESTDATA_DIR)
	p = os.path.join(TESTDATA_DIR, suite_to_dirname(suite))
	ensure_existence_directory(p)
	return p

def download_and_release(suite: str, tag: str = 'latest'):
	URL_ORGANIZATION = 'se-c-cpp-prog'
	URL_REPOSITORY = 'public-tests'

	win32 = is_windows()
	url = "https://github.com/%s/%s/releases/download/%s/%s-tests.%s" % (URL_ORGANIZATION, URL_REPOSITORY, ("%s-%s" % (suite, tag)), suite, ('zip' if win32 else 'tar.gz'))
	directory = make_suite_dirname(suite)
	output = wget.download(url)

	if win32:
		with zipfile.ZipFile(output, 'r') as zip:
			zip.extractall(directory)
	else:
		with tarfile.TarFile(output, 'r') as tar:
			tar.extractall(directory)

	os.remove(output)

def escape_envname(name: str) -> str:
	s = ''
	for c in name:
		if c == ' ' or c == '-':
			s += '_'
		elif c == '+':
			s += 'PLUS'
		elif c == '-':
			s += 'MINUS'
		elif c == '*':
			s += 'MULTIPLY'
		elif c == '/':
			s += 'DIVIDE'
		elif c == '(':
			s += '_LEFT_BRACKET_'
		elif c == ')':
			s += '_RIGHT_BRACKET_'
		else:
			s += c
	return s

def get_coefficients(suite_name: str, categories: Iterable[str]) -> Optional[Dict[str, float]]:
	PREFIX = 'SE_C_PROG'
	coefficients: Dict[str, float] = {}
	for category in categories:
		raw_value = os.getenv("%s_%s_%s" % (PREFIX, escape_envname(suite_name.upper()), escape_envname(category.upper())))
		if raw_value is None:
			return None
		coefficients[category] = float(raw_value)
	return coefficients

def escape(x: str) -> str:
	s = ''
	for c in x:
		if c == '\n':
			s += "\\n"
		elif c == '\r':
			s += "\\r"
		elif c == '\t':
			s += "\\t"
		elif c == '\\':
			s += "\\\\"
		else:
			s += c
	return s

def to_list(input: Union[str, int, float, List[str], List[int], List[float]], need_newline: bool = True) -> List[str]:
	if isinstance(input, (str, int, float)):
		l = [str(input)]
		if need_newline:
			l.append('')
		return l
	elif isinstance(input, list):
		l = [str(item) for item in input]
		if need_newline:
			l.append('')
		return l
	else:
		raise TypeError('Input must be a string, integer, float, or a list of strings, integers, or floats.')

def to_str(input: Union[str, int, float, List[str], List[int], List[float]], separator: str = '') -> str:
	if isinstance(input, (str, int, float)):
		return str(input)
	elif isinstance(input, list):
		return separator.join([str(item) for item in input])
	else:
		raise TypeError('Input must be a string, integer, float, or a list of strings, integers, or floats.')

def err_ok() -> BaseResult:
	return BaseResult(Errno.ERROR_SUCCESS)

def err_should_pass(exitcode: int) -> BaseResult:
	return BaseResult(Errno.ERROR_SHOULD_PASS, what = "program returned exitcode %d" % (exitcode))

def err_should_fail() -> BaseResult:
	return BaseResult(Errno.ERROR_SHOULD_FAIL, what = 'program returned exitcode = 0')

def err_stderr_empty() -> BaseResult:
	return BaseResult(Errno.ERROR_STDERR_EMPTY, what = 'program should write any human readable error message for user')

def err_stdout_not_empty(stdout: str) -> BaseResult:
	return BaseResult(Errno.ERROR_STDOUT_NOT_EMPTY, what = "stdout: \"%s\"" % (escape(stdout)))

def err_stderr_not_empty(stderr: str) -> BaseResult:
	return BaseResult(Errno.ERROR_STDERR_NOT_EMPTY, what = "stderr: \"%s\"" % (escape(stderr)))

def err_exitcode(actual_exitcode: int, expected_exitcode: int) -> BaseResult:
	return BaseResult(Errno.ERROR_EXITCODE, what = "expected %d, but actual %d" % (actual_exitcode, expected_exitcode))

def err_timeout() -> BaseResult:
	return BaseResult(Errno.ERROR_TIMEOUT)

def err_assertion_lines(actual: str, expected: str, lineno: int) -> BaseResult:
	if expected == '':
		return BaseResult(Errno.ERROR_ASSERTION, what = 'newline at the end of stream is necessary')
	return BaseResult(Errno.ERROR_ASSERTION, what = "on output line #%d expected was \"%s\", but actual is \"%s\"" % (lineno, escape(expected), escape(actual)))

def err_assertion_pos(i: int, j: int, actual: str, expected: str) -> BaseResult:
	return BaseResult(Errno.ERROR_ASSERTION, what = "at (row, column)=(%d, %d) position should be \"%s\", but actual is \"%s\"" % (i, j, expected, actual))

def err_assertion_len(actual_len: int, expected_len: int) -> BaseResult:
	return BaseResult(Errno.ERROR_ASSERTION, what = "the number of rows in the actual solution (%d) does not match the number of rows in the expected solution (%d)" % (actual_len, expected_len))

def err_file_not_found(file: str) -> BaseResult:
	return BaseResult(Errno.ERROR_FILE_NOT_FOUND, what = "file \"%s\" should be created after running program" % (file))

def err_file_created_on_error(file: str) -> BaseResult:
	return BaseResult(Errno.ERROR_FILE_CREATED_ON_ERROR, what = "file \"%s\" should not be created after program\'s failing" % (file))

def err_file_recreated_on_error(file: str) -> BaseResult:
	return BaseResult(Errno.ERROR_FILE_RECREATED_ON_ERROR, what = "file \"%s\" should be same as it was before program\'s failing" % (file))

def err_type_error(i: int, j: int, type_error_message: str) -> BaseResult:
	return BaseResult(Errno.ERROR_TYPE_ERROR, what = "at (row, column)=(%d, %d) position should be %s" % (i, j, type_error_message))

def err_no_newline() -> BaseResult:
	return BaseResult(Errno.ERROR_NO_NEWLINE)

def err_unknown(what: str) -> BaseResult:
	return BaseResult(Errno.ERROR_UNKNOWN, what = escape(what))

def get_time() -> int:
	return time.time_ns() // 1000000

def basic_compare_fn(actual: str, expected: str) -> bool:
	# Compare.
	return actual == expected

def basic_compare_bytes_fn(actual: bytes, expected: str) -> bool:
	# Compare.
	return actual == expected

class BaseMeta:
	def __init__(self, meta: Union[str, int, float, List[str], List[int], List[float]]):
		self.meta = meta

ContentT = Union[List[str], bytes, BaseMeta]

class BaseComparator:
	def __init__(self):
		pass

	def compare(self, actual: ContentT, expected: ContentT) -> BaseResult:
		if isinstance(actual, list) and isinstance(expected, list):
			return self._compare_details(actual, expected, basic_compare_fn, 'plain text (string)')
		elif isinstance(actual, bytes) and isinstance(expected, bytes):
			return self._compare_details_bytes(actual, expected, basic_compare_bytes_fn, 'bytes')
		elif isinstance(actual, BaseMeta) and isinstance(expected, BaseMeta):
			return err_ok() # should be always override
		else:
			raise TypeError("[FATAL ERROR] Expected lists of strings, raw byte sequences or meta's")

	def _compare_details_bytes(self, actual: bytes, expected: bytes, compare_fn: Callable[[bytes, bytes], bool], type_error_message: str) -> BaseResult:
		actual_len = len(actual)
		expected_len = len(expected)

		# CASE: fatal assertion.
		if actual_len != expected_len:
			return err_assertion_len(actual_len, expected_len)

		# CASE: assertion.
		try:
			if not compare_fn(actual, expected):
				return BaseResult(Errno.ERROR_ASSERTION, what = f"contents not same")
		except ValueError:
			return BaseResult(Errno.ERROR_ASSERTION, what = f"contents should be {type_error_message}")

		return err_ok()

	def _compare_details(self, actual: List[str], expected: List[str], compare_fn: Callable[[str, str], bool], type_error_message: str, assertion_message_fn: Callable[[int, int, str, str], BaseResult] = None) -> BaseResult:
		actual_len = len(actual)
		expected_len = len(expected)

		# CASE: fatal assertion.
		if actual_len != expected_len:
			return err_assertion_len(actual_len, expected_len)

		# CASE: assertion.
		for i in range(min(actual_len, expected_len)):
			actual_contents = actual[i].strip().split(' ')
			expected_contents = expected[i].strip().split(' ')

			actual_contents_len = len(actual_contents)
			expected_contents_len = len(expected_contents)

			# CASE: fatal assertion.
			if actual_contents_len != expected_contents_len:
				return err_assertion_len(actual_contents_len, expected_contents_len)

			# CASE: Newline, when it's only one element '', then newline found.
			if expected_contents_len == 1 and expected_contents[0] == '' and actual_contents[0] == '':
				continue
			elif expected_contents_len == 1 and expected_contents[0] == '' and actual_contents[0] != '':
				return err_no_newline()

			for j in range(min(actual_contents_len, expected_contents_len)):
				a = actual_contents[j]
				e = expected_contents[j]
				try:
					if not compare_fn(a, e):
						if assertion_message_fn is None:
							return err_assertion_pos(i, j, a, e)
						else:
							return assertion_message_fn(i, j, a, e)
				except ValueError:
					return err_type_error(i, j, type_error_message)

		return err_ok()

class BaseTest:
	def __init__(self,
			name: str,
			categories: Iterable[str],
			input: Union[str, int, float, List[str], List[int], List[float]],
			expected: Optional[Union[str, int, float, List[str], List[int], List[float]]],
			output_stream: Optional[str],
			timeout: float,
			exitcode: int,
			is_stdin_input: bool,
			is_raw_input: bool,
			is_raw_output: bool,
			input_separator: str,
			comparator: Optional[BaseComparator],
			testing_type: BaseTestingType
	):
		self.name = name
		self.categories = categories

		self.__input = input
		self.__expected = expected
		self.__output_stream = output_stream
		self.__timeout = timeout
		self.__exitcode = exitcode

		self.__is_stdin_input = is_stdin_input
		self.__is_raw_input = is_raw_input
		self.__is_raw_output = is_raw_output
		self.__input_separator = input_separator

		self.__comparator = comparator

		self.__testing_type = testing_type

		self.__passes = exitcode == 0

	# Returns None, if there was a timeout expired exception.
	# Otherwise, returns tuple of STDOUT, STDERR and RETURNCODE of program.
	def __runner(self, program: str, input: Union[str, int, float, List[str], List[int], List[float]], timeout: float, timeout_factor: float) -> Tuple[int, Optional[Tuple[str, str, int]]]:
		full_program = [program]
		full_timeout = timeout * timeout_factor

		# If it's not STDIN communication, turn input to list as cmd's arguments.
		if not self.__is_stdin_input:
			full_program += to_list(input, False)

		# If it's STDIN communication, then process should be created and then communicated.
		# Otherwise, run once.
		if self.__is_stdin_input:
			proc = subprocess.Popen(full_program, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, universal_newlines = True)
			start = get_time()
			try:
				if self.__is_raw_input:
					stdout, stderr = proc.communicate(to_str(input, self.__input_separator), timeout = full_timeout)
					end = get_time()
					return (end - start, (stdout, stderr, proc.returncode))
				else:
					file_content = ""
					if isinstance(input, str):
						with open(input, 'r') as stream:
							file_content = stream.read()
					else:
						raise ValueError('[FATAL ERROR] When it\'s stdin communication and not as raw string producer, then it should be path/to/file with wanted contents.')
					stdout, stderr = proc.communicate(file_content, timeout = full_timeout)
					end = get_time()
					return (end - start, (stdout, stderr, proc.returncode))
			except subprocess.TimeoutExpired:
				end = get_time()
				proc.kill()
				return (end - start, None)
		else:
			start = get_time()
			try:
				proc = subprocess.Popen(full_program, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, universal_newlines = True)
				stdout, stderr = proc.communicate(timeout = full_timeout)
				end = get_time()
				return (end - start, (stdout, stderr, proc.returncode))
			except subprocess.TimeoutExpired:
				end = get_time()
				proc.kill()
				return (end - start, None)

	def __collect_to_result(self, stdout: str, stderr: str, returncode: int, timer: int, base_result: BaseResult) -> BaseResult:
		base_result.testing_type = self.__testing_type
		base_result.output = stdout

		if self.__output_stream is not None:
			if not os.path.exists(self.__output_stream):
				base_result.output = None
			else:
				if self.__testing_type == BaseTestingType.T_TEXT:
					with open(self.__output_stream, 'r') as file:
						base_result.output = file.read()
				elif self.__testing_type == BaseTestingType.T_BINARY:
					with open(self.__output_stream, 'rb') as file:
						base_result.output = file.read()

		base_result.stderr = stderr
		base_result.timer = timer
		base_result.exitcode = returncode

		return base_result

	def __should_pass(self, stdout: str, stderr: str, returncode: int, check_output: bool) -> BaseResult:
		# CASE: Program doesn't returns 0.
		empty_stderr = stderr == "" or stderr is None
		if returncode != 0:
			# For sanitizers.
			if not empty_stderr:
				print('       STDERR -->')
				print(stderr)
				print('   <-- STDERR')
			return err_should_pass(returncode)

		# If there is no point to check output, then skip and return OK.
		if not check_output:
			# For sanitizers.
			if not empty_stderr:
				print('       STDERR -->')
				print(stderr)
				print('   <-- STDERR')
			return err_ok()

		# CASE: Error output should be empty.
		if not empty_stderr:
			return err_stderr_not_empty(stderr)

		# Read actual content.
		actual_content: ContentT = None
		if self.__testing_type == BaseTestingType.T_TEXT:
			if self.__output_stream is None:
				actual_content = stdout.split('\n')
			else:
				if not os.path.exists(self.__output_stream):
					return err_file_not_found(self.__output_stream)
				with open(self.__output_stream, 'r') as file:
					actual_content = file.read().split('\n')
		elif self.__testing_type == BaseTestingType.T_BINARY and self.__output_stream is not None:
			if not os.path.exists(self.__output_stream):
				return err_file_not_found(self.__output_stream)
			with open(self.__output_stream, 'rb') as file:
				actual_content = file.read()
		elif self.__testing_type == BaseTestingType.T_META and self.__output_stream is None:
			actual_content = BaseMeta(self.__input)
		else:
			raise ValueError("[FATAL ERROR] Testing type is not exists or incompatible combination with output stream")

		# Read expected content.
		expected_content: ContentT = None
		if self.__is_raw_output and self.__testing_type == BaseTestingType.T_TEXT:
			expected_content = to_list(self.__expected)
		elif self.__testing_type == BaseTestingType.T_BINARY or self.__testing_type == BaseTestingType.T_TEXT:
			if not isinstance(self.__expected, str):
				raise ValueError('[FATAL ERROR] When it\'s not raw string producer, then it should be path/to/file with wanted contents.')
			if self.__testing_type == BaseTestingType.T_TEXT:
				with open(self.__expected, 'r') as file:
					expected_content = file.read().split('\n')
			else:
				with open(self.__expected, 'rb') as file:
					expected_content = file.read()
		elif self.__testing_type == BaseTestingType.T_META:
			expected_content = BaseMeta(self.__expected)

		# CASE: assertion.
		return self.__comparator.compare(actual_content, expected_content)

	def __should_fail(self, stdout: str, stderr: str, returncode: int) -> BaseResult:
		# CASE: Program returns 0.
		if returncode == 0:
			return err_should_fail()

		empty_stderr = stderr == "" or stderr is None
		empty_stdout = stdout == "" or stdout is None

		# CASE: Should be error message.
		if empty_stderr:
			return err_stderr_empty()

		# CASE: Output should be empty.
		if not empty_stdout:
			return err_stdout_not_empty(stdout)

		# CASE: Exitcode must be correct.
		if returncode != self.__exitcode:
			# For sanitizers.
			if not empty_stderr:
				print('       STDERR -->')
				print(stderr)
				print('   <-- STDERR')
			return err_exitcode(returncode, self.__exitcode)

		return err_ok()

	def run(self, program: str, check_output: bool, timeout_factor: float) -> BaseResult:
		try:
			timer, results = self.__runner(program, self.__input, self.__timeout, timeout_factor)

			# If it's None, then there was a Timeout error.
			if results is None:
				timeout_result = err_timeout()
				timeout_result.timer = timer
				timeout_result.exitcode = -1
				timeout_result.testing_type = self.__testing_type
				return timeout_result

			stdout, stderr, returncode = results

			if self.__passes:
				should_pass_result = self.__should_pass(stdout, stderr, returncode, check_output)
				return self.__collect_to_result(stdout, stderr, returncode, timer, should_pass_result)

			should_fail_result = self.__should_fail(stdout, stderr, returncode)
			return self.__collect_to_result(stdout, stderr, returncode, timer, should_fail_result)
		except Exception as e:
			result = err_unknown(str(e))
			result.testing_type = self.__testing_type
			return result

	def get_input(self) -> str:
		input_content = to_str(self.__input, ' ')
		if not self.__is_raw_input:
			with open(str(self.__input), 'r') as stream:
				input_content = stream.read()
		return input_content

	def get_reference(self) -> str:
		if self.__expected is None:
			return None
		expected_content = to_str(self.__expected, ' ')
		if not self.__is_raw_output:
			with open(str(self.__expected), 'r') as file:
				expected_content = file.read()
		return expected_content

class BaseSuite:
	def __init__(self):
		self.__results: List[Tuple[BaseTest, BaseResult]] = []

	def add_result(self, test: BaseTest, result: BaseResult):
		self.__results.append((test, result))

	def ok(self) -> bool:
		return all(result.ok() for _, result in self.__results)

	def __get_number_passed(self, category: str) -> int:
		passed = 0
		for results in self.__results:
			test, result = results
			if result.ok() and category in test.categories:
				passed += 1
		return passed

	def __get_number_total(self, category: str) -> int:
		total = 0
		for results in self.__results:
			test, _ = results
			if category in test.categories:
				total += 1
		return total

	def get_all_categories(self) -> Set[str]:
		all_categories: Set[str] = set()
		for results in self.__results:
			test, _ = results
			all_categories.update(test.categories)
		return all_categories

	def get_raw_results(self) -> Dict[str, float]:
		raw: Dict[str, float] = {}
		categories = self.get_all_categories()

		for category in categories:
			passed = self.__get_number_passed(category)
			total = self.__get_number_total(category)
			raw[category] = (passed / total)

		return raw

	def json(self) -> Dict[str, dict]:
		json_results: Dict[str, dict] = {}
		for i, results in enumerate(self.__results):
			test, result = results
			json_object_name = "test_%d" % (i)
			json_single_result = {}
			json_single_result['categories'] = list(test.categories)
			json_single_result['passed'] = result.ok()
			json_single_result['verdict'] = result.get_verdict()
			additional_info = result.get_additional_info()
			if additional_info is not None:
				json_single_result['verdict_additional_info'] = additional_info
			json_single_result['name'] = test.name
			json_single_result['input'] = test.get_input()
			if result.testing_type == BaseTestingType.T_TEXT:
				json_single_result['output'] = '<no output>' if result.output is None or result.output == '' else result.output
			elif result.testing_type == BaseTestingType.T_BINARY:
				json_single_result['output'] = '<no output>' if result.output is None or result.output == '' else '<raw bytes>'
			elif result.testing_type == BaseTestingType.T_META:
				json_single_result['output'] = '<very meta info>'
			if result.testing_type == BaseTestingType.T_TEXT:
				reference_str = test.get_reference()
				json_single_result['reference'] = '<no reference>' if reference_str is None or reference_str == '' else reference_str
			else:
				json_single_result['reference'] = '<no reference>'
			json_single_result['stderr'] = '<no error output>' if result.stderr is None or result.stderr == '' else result.stderr
			json_single_result['exitcode'] = result.exitcode
			json_single_result['time'] = result.timer
			json_results[json_object_name] = json_single_result
		return json_results

class BaseTester:
	def __init__(self, is_stdin_input: bool = True, is_raw_input: bool = True, is_raw_output: bool = True, input_separator: str = ' ', testing_type: BaseTestingType = BaseTestingType.T_TEXT):
		self.__is_stdin_input = is_stdin_input
		self.__is_raw_input = is_raw_input
		self.__is_raw_output = is_raw_output
		self.__input_separator = input_separator
		self.__testing_type = testing_type
		self.__tests: List[BaseTest] = []

		# Not RAW input with not STDIN communication sounds strange.
		if not self.__is_stdin_input and not self.__is_raw_input:
			raise NotImplementedError('[FATAL ERROR] Not raw input (from file) with cmd\'s arguments communication is not supported yet.')

	def add_success(self, name: str, input: Union[str, int, float, List[str], List[int], List[float]], expected: Union[str, int, float, List[str], List[int], List[float]], output_stream: str = None, timeout: float = 1.0, categories: Iterable[str] = [], comparator: BaseComparator = BaseComparator()):
		test = BaseTest(name, categories, input, expected, output_stream, timeout, 0, self.__is_stdin_input, self.__is_raw_input, self.__is_raw_output, self.__input_separator, comparator, self.__testing_type)
		self.__tests.append(test)

	def add_failed(self, name: str, input: Union[str, int, float, List[str], List[int], List[float]], exitcode: int, timeout: float = 1.0, categories: Iterable[str] = []):
		test = BaseTest(name, categories, input, None, None, timeout, exitcode, self.__is_stdin_input, self.__is_raw_input, self.__is_raw_output, self.__input_separator, None, self.__testing_type)
		self.__tests.append(test)

	def run(self, program: str, check_output: bool, timeout_factor: float) -> BaseSuite:
		# If there is no file, then no test.
		if not os.path.exists(program):
			raise FileNotFoundError("[FATAL ERROR] File (executable) named \"%s\" not found." % (program))

		suite = BaseSuite()
		for test in self.__tests:
			print("-- Performing %s..." % (test.name))
			result = test.run(program, check_output, timeout_factor)
			print(result)
			suite.add_result(test, result)

		return suite

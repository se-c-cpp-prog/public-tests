import os
import shutil
import numpy as np

import testsuites.base as base

from enum import Enum
from typing import Tuple, Optional, Dict, Iterable, List, Union

SUITE_NAME = 'invertible-matrix'
__SUITE_DIR = base.make_suite_dirname(SUITE_NAME)

__ALL_GOOD_CATEGORIES = ['eye', 'diag', 'normal', 'ort', 'frac', 'triangle']
__ALL_BAD_CATEGORIES = ['neg']

__ALL_CATEGORIES = __ALL_GOOD_CATEGORIES + __ALL_BAD_CATEGORIES

# (<subdir name>, <file ext>)
class __TestType(Enum):
	IN = ('in', 'in')
	OUT = ('out', 'out')
	REF = ('ref', 'out')

# Actual vs. expected matrix comparator.
class __GoodComparator(base.BaseComparator):
	def __init__(self):
		pass

	def compare(self, actual: List[str], expected: List[str]) -> base.BaseResult:
		DELTA = 1e-4

		if len(actual) != len(expected):
			return base.err_assertion_len(len(actual), len(expected))

		# Remove empty (newline) element.
		actual.pop()
		expected.pop()

		# Comparison header.
		out_header = actual[0]
		ref_header = expected[0]
		r = 0
		c = 0
		try:
			out_r, out_c = map(int, out_header.split(' '))
			ref_r, ref_c = map(int, ref_header.split(' '))
			if out_r != ref_r or out_c != ref_c:
				return base.BaseResult(
							base.Errno.ERROR_ASSERTION,
							what = "expected matrix size (%d %d) is not equals to actual (%d %d)" % (ref_r, ref_c, out_r, out_c)
				)
			r = ref_r
			c = ref_c
		except ValueError:
			return base.BaseResult(base.Errno.ERROR_TYPE_ERROR, what = "R/C should be integers")

		# Comparison matrices.
		nested_actual_matrix = [s.strip().split(' ') for s in actual[1:]]
		nested_expected_matrix = [s.strip().split(' ') for s in expected[1:]]

		for i in range(r):
			if len(nested_actual_matrix[i]) != len(nested_expected_matrix[i]):
				return base.BaseResult(
					base.Errno.ERROR_ASSERTION,
					what = "expected number of columns %d on row #%d is not equals to actual (%d)" % (len(nested_expected_matrix[i]), i, len(nested_actual_matrix[i]))
				)

		actual_matrix = np.array([[float(j) for j in i] for i in nested_actual_matrix])
		expected_matrix = np.array([[float(j) for j in i] for i in nested_expected_matrix])

		max_abs = np.fmax(np.abs(expected_matrix), np.abs(actual_matrix))
		max_by_row = np.amax(max_abs, axis = 1)
		max_by_col = np.amax(max_abs, axis = 0)

		for y in range(r):
			for x in range(c):
				a = actual_matrix[y][x]
				e = expected_matrix[y][x]
				diff = abs(a - e)
				m = min(max_by_row[y], max_by_col[x])
				d = diff / m
				if d > DELTA:
					return base.BaseResult(
						base.Errno.ERROR_ASSERTION,
						what = "at (row, column)=(%d, %d) position should be %f (+/-%f), but found %f" % (y, x, float(e), DELTA, float(a))
					)

		return base.err_ok()

def __make_basename(type: __TestType, name: Union[int, str]) -> str:
	return "test_%s.%s" % (str(name), type.value[1])

def __make_categorized_basename(category: str, type: __TestType, name: Union[int, str]) -> str:
	return os.path.join(category.replace(' ', '_'), __make_basename(name, type))

def __make_subdir_basename(category: str, type: __TestType, name: Optional[Union[int, str]] = None) -> str:
	if name is None:
		return os.path.join(type.value[0], category.replace(' ', '_'))
	else:
		return os.path.join(type.value[0], __make_categorized_basename(category, name, type))

def __make_in_basename(category: str, name: Optional[Union[int, str]] = None) -> str:
	return __make_subdir_basename(category, __TestType.IN, name)

def __make_out_basename(category: str, name: Optional[Union[int, str]] = None) -> str:
	return __make_subdir_basename(category, __TestType.OUT, name)

def __make_ref_basename(category: str, name: Optional[Union[int, str]] = None) -> str:
	return __make_subdir_basename(category, __TestType.REF, name)

def __make_in_path(category: str, name: Optional[Union[int, str]] = None) -> str:
	return os.path.join(__SUITE_DIR, __make_in_basename(category, name))

def __make_out_path(category: str, name: Optional[Union[int, str]] = None) -> str:
	return os.path.join(__SUITE_DIR, __make_out_basename(category, name))

def __make_ref_path(category: str, name: Optional[Union[int, str]] = None) -> str:
	return os.path.join(__SUITE_DIR, __make_ref_basename(category, name))

def __write_mtx(mtx, filename: str, fmt: str = '%g'):
	rows, cols = mtx.shape
	with open(filename, 'w') as f:
		f.write(f"{rows} {cols}\n")
		np.savetxt(f, mtx, fmt = fmt)

def __read_mtx(filename: str, dtype = float):
	with open(filename, "r") as f:
		_, cols = f.readline().split()
	m_n = range(int(cols))
	m = np.loadtxt(filename, dtype = dtype, delimiter = " ", skiprows = 1, usecols = (m_n), ndmin = 2)
	return m

def __create_test_files(test_case: str, test_idx: int, mtx, fmt: str = '%g') -> Tuple[str, str, str]:
	input_mtx_file = __make_in_path(test_case, test_idx)
	__write_mtx(mtx, input_mtx_file, fmt = fmt)
	ref_mtx_file = __make_ref_path(test_case, test_idx)
	inverted_mtx = np.linalg.inv(__read_mtx(input_mtx_file))
	__write_mtx(inverted_mtx, ref_mtx_file, fmt = fmt)
	return input_mtx_file, __make_out_path(test_case, test_idx), ref_mtx_file

def __cleanup(path: str):
	if os.path.exists(path):
		shutil.rmtree(path)
	base.ensure_existence_directory(path)

def __full_cleanup(category: str):
	__cleanup(__make_in_path(category))
	__cleanup(__make_ref_path(category))
	__cleanup(__make_out_path(category))

def __generate_bad_tests() -> Iterable[Tuple[str, str, str, int]]:
	generated: List[Tuple[str, str, str, int]] = []

	category = 'neg'

	empty_file_raw_input = __make_in_path(category, 1)
	with open(empty_file_raw_input, 'w') as file:
		file.write('\n')
	test_data = ('Empty file', category, empty_file_raw_input, 1)
	generated.append(test_data)

	return generated

def __generate_good_tests() -> Iterable[Tuple[str, str, str, str, str, base.BaseComparator]]:
	generated: List[Tuple[str, str, str, str, str, base.BaseComparator]] = []

	category = 'eye'
	__full_cleanup(category)
	sizes_1 = [1, 2, 5, 11, 26, 51, 73, 100]
	for i in range(len(sizes_1)):
		m = np.eye(sizes_1[i])
		raw_input, raw_output, raw_expected = __create_test_files(category, i, m)
		test_data = (f"{category.capitalize()} #{i}", category, raw_input, raw_output, raw_expected, __GoodComparator)
		generated.append(test_data)

	category = 'diag'
	__full_cleanup(category)
	sizes_2 = [1, 5, 23, 44, 53, 78, 100]
	for i in range(len(sizes_2)):
		m = np.eye(sizes_2[i])
		for j in range(sizes_2[i]):
			m[j][j] = np.random.randint(-100, 100)
			if m[j][j] == 0:
				m[j][j] = 1
		raw_input, raw_output, raw_expected = __create_test_files(category, i, m)
		test_data = (f"{category.capitalize()} #{i}", category, raw_input, raw_output, raw_expected, __GoodComparator)
		generated.append(test_data)

	category = 'normal'
	__full_cleanup(category)
	sizes_3 = [2, 3, 5, 7, 11,
			  13, 17, 19, 23, 29,
			  31, 37, 41, 43, 47,
			  53, 59, 61, 67, 71,
			  73, 79, 83, 89, 93,
			  97, 101, 103, 110]
	for i in range(len(sizes_3)):
		m = np.zeros((sizes_3[i], sizes_3[i]))
		while np.linalg.det(m) == 0:
			for j in range(sizes_3[i]):
				for k in range(sizes_3[i]):
					m[j][k] = np.random.randint(-100, 100)
		raw_input, raw_output, raw_expected = __create_test_files(category, i, m)
		test_data = (f"{category.capitalize()} #{i}", category, raw_input, raw_output, raw_expected, __GoodComparator)
		generated.append(test_data)

	category = 'ort'
	__full_cleanup(category)
	sizes_4 = [1, 7, 24, 56, 77, 102]
	for i in range(len(sizes_4)):
		m = np.zeros((sizes_4[i], sizes_4[i]))
		while np.linalg.det(m) == 0:
			for j in range(sizes_4[i]):
				m[j][sizes_4[i] - j - 1] = np.random.randint(-100, 100)
		raw_input, raw_output, raw_expected = __create_test_files(category, i, m)
		test_data = (f"{category.capitalize()} #{i}", category, raw_input, raw_output, raw_expected, __GoodComparator)
		generated.append(test_data)

	category = 'frac'
	__full_cleanup(category)
	sizes_5 = [3, 4, 6, 9, 12,
			  15, 18, 20, 24, 30,
			  34, 38, 42, 46, 50,
			  55, 60, 64, 82, 85, 90]
	for i in range(len(sizes_5)):
		m = np.zeros((sizes_5[i], sizes_5[i]))
		while np.linalg.det(m) == 0:
			for j in range(sizes_5[i]):
				for k in range(sizes_5[i]):
					m[j][k] = np.random.uniform(-100, 100)
		raw_input, raw_output, raw_expected = __create_test_files(category, i, m)
		test_data = (f"{category.capitalize()} #{i}", category, raw_input, raw_output, raw_expected, __GoodComparator)
		generated.append(test_data)

	category = 'triangle'
	__full_cleanup(category)
	sizes_6 = [4, 7, 11, 22, 30,
			   3, 5, 6, 7, 8,
			   5, 8, 14, 35, 45,
			   4, 5, 6, 7, 8]
	for i in range(len(sizes_6)):
		m = np.zeros((sizes_6[i], sizes_6[i]))
		while np.linalg.det(m) == 0:
			for j in range(sizes_6[i]):
				for k in range(j, sizes_6[i]):
					if i < 5:
						m[j][k] = np.random.uniform(-50, 50)
					elif i < 10:
						m[k][j] = np.random.uniform(-10, 10)
					elif i < 15:
						m[sizes_6[i] - j - 1][k] = np.random.uniform(-100, 100)
					elif i < 20:
						m[j][sizes_6[i] - k - 1] = np.random.uniform(-100, 100)
		raw_input, raw_output, raw_expected = __create_test_files(category, i, m)
		test_data = (f"{category.capitalize()} #{i}", category, raw_input, raw_output, raw_expected, __GoodComparator)
		generated.append(test_data)

	def __hilbert_matrix(n: int):
		return np.array([[1 / (i + j + 1) for j in range(n)] for i in range(n)])

	sizes_7 = [3, 4]
	for i in range(len(sizes_7)):
		m = __hilbert_matrix(sizes_7[i])
		raw_input, raw_output, raw_expected = __create_test_files('frac', i + len(sizes_5), m, '%.12g')
		test_data = (f"{category.capitalize()} #{i}", category, raw_input, raw_output, raw_expected, __GoodComparator)
		generated.append(test_data)

	category = 'neg'
	__full_cleanup(category)
	neg_mtx = [
		np.array([[-76, 98]]),
		np.array([[20, 54, -49, 75], [47, 31, 67, -61], [13, 68, -97, 24], [41, -53, 13, 46], [-12, -77, 10, -90]]),
		np.array([[-64, 15, -57, 48, 89], [99, -72, 19, -20, 16], [-10, 50, 68, 62, -46], [99, -72, 19, -20, 16], [-10, 50, 68, 62, -46]]),
		np.array([[47, 27, 9, 5, -2, 28, 30, -19, 30, -19], [66, 85, 36, -49, 43, -48, -99, -24, -99, -24], [61, 28, 56, 75, 18, -59, -56, -79, -56, -79], [-56, -41, 60, -53, -42, -11, 62, -87, 62, -87], [-20, 11, -43, -48, -24, -28, -53, -36, -53, -36], [83, 29, -68, 7, -89, -47, 54, -68, 54, -68], [-63, -12, 10, -75, 32, 80, -99, 3, -99, 3], [20, -31, -9, 6, 13, 87, -47, 65, -47, 65], [-95, 90, 67, -59, -77, -67, -43, -76, -43, -76], [-42, -6, -92, -62, -98, 48, -42, 35, -42, 35]]),
		np.array([[-69, 0, -48, -86, 54, 23, 84, -35, -86, 2, -4, -67, 14, -67, 14], [62, -69, -93, -69, -67, 28, -68, 72, 78, 42, 30, 20, 59, 20, 59], [58, 80, 54, 83, 41, -3, -54, 61, -38, 17, -58, 74, -100, 74, -100], [28, 40, -55, 91, -75, -7, -85, 99, -82, 56, 84, -4, -34, -4, -34], [-43, -62, 36, 31, 92, -38, -86, -13, 8, -9, -96, -93, -100, -93, -100], [7, 75, 62, -4, 84, -86, 25, -9, 76, 56, -39, -40, 8, -40, 8], [32, 1, -80, -2, -8, -19, 30, -100, -6, 88, -76, -20, -24, -20, -24], [13, -15, 94, 80, -32, -25, -1, 13, -92, 26, 77, -27, -29, -27, -29], [-94, 76, -80, -15, -61, 48, -29, 58, -33, 64, 61, -17, 88, -17, 88], [-56, -32, -2, -12, -36, 58, 4, 0, -21, -2, -44, 4, -11, 4, -11], [21, -61, 2, 50, 73, -62, -4, -6, 22, 74, 70, 93, 47, 93, 47], [-98, 78, 72, -86, 59, -73, 37, 93, -39, 67, 43, 38, -76, 38, -76], [35, -14, 58, -26, 71, 43, -74, -63, 91, -56, 39, -34, 29, -34, 29], [53, 78, 42, -72, -77, 13, 35, 62, -28, -26, 13, 76, 54, 76, 54], [15, 94, 34, -24, 12, 16, 50, -32, -57, -45, -21, 24, -49, 24, -49]]),
		np.zeros((20, 20))
	]
	for i, m in enumerate(neg_mtx):
		raw_input = __make_in_path(category, i + 2)
		raw_output = __make_out_path(category, i + 2)
		raw_expected = __make_ref_path(category, i + 2)
		__write_mtx(m, raw_input)
		with open(raw_expected, 'w') as file:
			file.write('no_solution\n')
		test_data = (f"{category.capitalize()} #{i + 2}", category, raw_input, raw_output, raw_expected, base.BaseComparator)
		generated.append(test_data)

	return generated

def get_instance() -> Tuple[base.BaseTester, Optional[Dict[str, float]]]:
	TIMEOUT = 0.5

	invertible_matrix_tester = base.BaseTester(is_stdin_input = False, is_raw_input = True, is_raw_output = False)

	good_tests = __generate_good_tests()
	bad_tests = __generate_bad_tests()
	coefficients = base.get_coefficients(SUITE_NAME, __ALL_CATEGORIES)

	for test_data in good_tests:
		test_name, test_category, test_input, test_output, test_expected, test_comparator = test_data
		invertible_matrix_tester.add_success(test_name, [test_input, test_output], test_expected, test_output, categories = [test_category], comparator = test_comparator(), timeout = TIMEOUT)

	for test_data in bad_tests:
		test_name, test_category, test_input, test_exitcode = test_data
		invertible_matrix_tester.add_failed(test_name, [test_input, "non_existing.out"], test_exitcode, timeout = TIMEOUT, categories = [test_category])

	return invertible_matrix_tester, coefficients

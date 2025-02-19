import os
import shutil
from PIL import Image, ImageChops

import testsuites.base as base

from enum import Enum
from typing import Tuple, Optional, Dict, Iterable, List, Union

SUITE_NAME = 'png'
__SUITE_DIR = base.make_suite_dirname(SUITE_NAME)

__ALL_GOOD_CATEGORIES = ['palette2rgb', 'gray2rgb', 'rgb2palette', 'rgb2gray']
__ALL_BAD_CATEGORIES = ['neg']

__ALL_CATEGORIES = __ALL_GOOD_CATEGORIES + __ALL_BAD_CATEGORIES

# (<subdir name>
class TestType(Enum):
	IN = 'in'
	OUT = 'out'
	REF = 'ref'
	REF_TMP = 'ref_tmp'

__TestType = TestType

# Actual vs. expected matrix comparator.
class __GoodComparator(base.BaseComparator):
	__PILType = { "RGB": 2, "L": 0, "P": 3 }
	__TestType = TestType

	def __init__(self):
		pass

	def compare(self, actual: base.ContentT, expected: base.ContentT) -> base.BaseResult:
		if not isinstance(actual, base.BaseMeta) or not isinstance(expected, base.BaseMeta) or not isinstance(actual.meta, list) or not isinstance(expected.meta, str):
			raise ValueError("[FATAL ERROR] For testing PNG there should be meta information in comparator")

		actual_file = actual.meta[1]
		expected_file = expected.meta

		actual_image = Image.open(actual_file)
		actual_format, actual_size, actual_mode = actual_image.format, actual_image.size, actual_image.mode

		if actual_format != 'PNG':
			return base.BaseResult(base.Errno.ERROR_TYPE_ERROR, what = f"output file '{actual_file}' is not PNG")
		
		if actual_mode != 'RGB' and "_rgb." in expected_file:
			return base.BaseResult(base.Errno.ERROR_TYPE_ERROR, what = f"expected RGB (colortype 2) image, but actual output file '{actual_file}' is {self.__PILType[actual_mode]} mode")

		if actual_mode != 'L' and "_gray." in expected_file:
			return base.BaseResult(base.Errno.ERROR_TYPE_ERROR, what = f"expected grayscale (colortype 0) image, but actual output file '{actual_file}' is {self.__PILType[actual_mode]} mode")

		if actual_mode != 'P' and "_plt." in expected_file:
			return base.BaseResult(base.Errno.ERROR_TYPE_ERROR, what = f"expected paletted (colortype 3) image, but actual output file '{actual_file}' is {self.__PILType[actual_mode]} mode")

		actual_image.convert('RGB').save(actual_file + ".ppm", format="PPM")
		
		expected_image = Image.open(expected_file)
		renamed_expected_file = expected_file.replace(os.path.join('png', self.__TestType.REF.value), os.path.join('png', self.__TestType.REF_TMP.value))
		expected_image.convert('RGB').save(renamed_expected_file + ".ppm", format = "PPM")

		ppm_actual_image = Image.open(actual_file + ".ppm")
		ppm_expected_image = Image.open(renamed_expected_file + ".ppm")

		diff = ImageChops.difference(ppm_actual_image, ppm_expected_image)
		channels = diff.split()
		for channel in channels:
			if channel.getbbox() is not None:
				return base.BaseResult(base.Errno.ERROR_ASSERTION, what = f"expected != actual, see raw images: expected '{renamed_expected_file + '.ppm'}', actual '{actual_file + '.ppm'}'")

		return base.err_ok()

def __make_basename(type: __TestType, name: Union[int, str]) -> str:
	return "%s" % (str(name))

def __make_categorized_basename(category: str, type: __TestType, name: Union[int, str]) -> str:
	return os.path.join(category.replace(' ', '_'), __make_basename(name, type))

def __make_subdir_basename(category: str, type: __TestType, name: Optional[Union[int, str]] = None) -> str:
	if name is None:
		return os.path.join(type.value, category.replace(' ', '_'))
	else:
		return os.path.join(type.value, __make_categorized_basename(category, name, type))

def __make_in_basename(category: str, name: Optional[Union[int, str]] = None) -> str:
	return __make_subdir_basename(category, __TestType.IN, name)

def __make_out_basename(category: str, name: Optional[Union[int, str]] = None) -> str:
	return __make_subdir_basename(category, __TestType.OUT, name)

def __make_ref_basename(category: str, name: Optional[Union[int, str]] = None) -> str:
	return __make_subdir_basename(category, __TestType.REF, name)

def __make_ref_tmp_basename(category: str, name: Optional[Union[int, str]] = None) -> str:
	return __make_subdir_basename(category, __TestType.REF_TMP, name)

def __make_in_path(category: str, name: Optional[Union[int, str]] = None) -> str:
	return os.path.join(__SUITE_DIR, __make_in_basename(category, name))

def __make_out_path(category: str, name: Optional[Union[int, str]] = None) -> str:
	return os.path.join(__SUITE_DIR, __make_out_basename(category, name))

def __make_ref_path(category: str, name: Optional[Union[int, str]] = None) -> str:
	return os.path.join(__SUITE_DIR, __make_ref_basename(category, name))

def __make_ref_tmp_path(category: str, name: Optional[Union[int, str]] = None) -> str:
	return os.path.join(__SUITE_DIR, __make_ref_tmp_basename(category, name))


def __cleanup(path: str):
	if os.path.exists(path):
		shutil.rmtree(path)
	base.ensure_existence_directory(path)

def __full_cleanup(category: str):
	__cleanup(__make_out_path(category))
	__cleanup(__make_ref_tmp_path(category))

def __generate_bad_tests() -> Iterable[Tuple[str, str, str, int]]:
	generated: List[Tuple[str, str, str, int]] = []

	category = 'neg'
	__full_cleanup(category)
	tests = [
		[ "ngjaba_neg_rgb.png", 1], # Too many colors for palette
		[ "ngjaba_neg.png", 1], # Colortype 1
		[ "nevyspyshi.png", 1], # 16 bits/sample
	]

	__full_cleanup(category)
	for i, t in enumerate(tests):
		test_data = (f"{category} #{i + 1}: '{t[0]}'", category,
						 __make_in_path(category, t[0]), t[1])
		generated.append(test_data)
	return generated

def __generate_good_categorized_tests(category: str, tests: List[str]):
	cat_generated = []
	__full_cleanup(category)
	for i, t in enumerate(tests):
		input_png_file = __make_in_path(category, t[0])
		ref_png_file = __make_ref_path(category, t[1])
		out_png_file = __make_out_path(category, t[1])

		test_data = (f"{category} #{i + 1}: '{t[0]}' -> '{t[1]}'", category,
						input_png_file, out_png_file, ref_png_file)
		cat_generated.append(test_data)
	return cat_generated

def __generate_good_tests() -> Iterable[Tuple[str, str, str, str, str, base.BaseComparator]]:
	generated: List[Tuple[str, str, str, str, str, base.BaseComparator]] = []
	
	generated += __generate_good_categorized_tests("palette2rgb", [
		["sphere2_plt.png", "sphere2_rgb.png"],
		["niconiconi_plt.png", "niconiconi_rgb.png"],
		["minipalette_plt.png", "minipalette_rgb.png"],
		["nogood_plt.png", "nogood_rgb.png"],
		["ngjaba_plt.png", "ngjaba_rgb.png"],
	])

	generated += __generate_good_categorized_tests("gray2rgb", [
		["nogood_gray.png", "nogood_rgb.png"],
	])

	generated += __generate_good_categorized_tests("rgb2palette", [
		["ngjaba_rgb.png", "ngjaba_plt.png"],
		["color_simple_PLTE_rgb.png", "color_simple_PLTE_plt.png"],
		["sphere2_rgb.png", "sphere2_plt.png"],
	])

	generated += __generate_good_categorized_tests("rgb2gray", tests = [
		["nogood_rgb.png", "nogood_gray.png"],
	])
	return generated

def get_instance() -> Tuple[base.BaseTester, Optional[Dict[str, float]]]:
	TIMEOUT = 1.0

	png_tester = base.BaseTester(is_stdin_input = False, is_raw_input = True, is_raw_output = False, testing_type = base.BaseTestingType.T_META)

	good_tests = __generate_good_tests()
	bad_tests = __generate_bad_tests()
	coefficients = base.get_coefficients(SUITE_NAME, __ALL_CATEGORIES)

	for test_data in good_tests:
		test_name, test_category, test_input, test_output, test_expected = test_data
		png_tester.add_success(test_name, [test_input, test_output], test_expected, categories = [test_category], comparator = __GoodComparator(), timeout = TIMEOUT)

	for test_data in bad_tests:
		test_name, test_category, test_input, test_exitcode = test_data
		png_tester.add_failed(test_name, [test_input, test_output], test_exitcode, categories = [test_category], timeout = TIMEOUT)

	return png_tester, coefficients

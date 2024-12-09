#!/usr/bin/env python3

import argparse
import os
import json
import random
import string

from typing import Dict, Tuple, Optional

import testsuites.base as base
import testsuites.sum as suite_sum
import testsuites.invertible_matrix as suite_invertible_matrix
import testsuites.sprintf as suite_sprintf
import testsuites.expression as suite_expression
import testsuites.png as suite_png

SELECTOR: Dict[str, Tuple[base.BaseTester, Optional[Dict[str, float]]]] = {
	suite_sum.SUITE_NAME: suite_sum.get_instance(),
	suite_invertible_matrix.SUITE_NAME: suite_invertible_matrix.get_instance(),
	suite_sprintf.SUITE_NAME: suite_sprintf.get_instance(),
	suite_expression.SUITE_NAME: suite_expression.get_instance(),
	suite_png.SUITE_NAME: suite_png.get_instance()
}

def __t_or_f(arg: str, flag_name: str) -> bool:
	ua = str(arg).upper()
	if ua == 'TRUE':
		return True
	elif ua == 'FALSE':
		return False
	else:
		print("usage: --%s [True|False]." % (flag_name))
		exit(1)

def __calculate_final_sum(results: base.BaseSuite, coefficients: Dict[str, float]) -> Optional[float]:
	if coefficients is None or len(coefficients) == 0:
		return 0.0
	n_categories = len(coefficients)
	f_sum = 0.0
	raw_results = results.get_raw_results()
	for category, coefficient in coefficients.items():
		if category not in raw_results:
			continue
		raw = raw_results[category]
		f_sum += coefficient * raw
	return f_sum / n_categories

def __generate_unique_filename() -> str:
	while True:
		random_part = ''.join(random.choices(string.ascii_letters + string.digits, k = 10))
		filepath = "%s.json" % (random_part)

		# Check if the file already exists
		if not os.path.exists(filepath):
			return filepath

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--program', help = 'path to the program under test', type = str, required = True)
	parser.add_argument('--suite', help = 'select testing task', type = str, choices = SELECTOR, required = True)
	parser.add_argument('--check-output', help = 'is it necessary to check the program\'s output', type = str, default = 'TRUE')
	parser.add_argument('--timeout-factor', help = 'maximum execution time multiplier', type = float, default = 1.0)
	parser.add_argument('--json-quick', help = 'JSON results: quick generating output filename, run target system, used compile for building program, build type compiled and run program for quick testing', type = str, default = 'FALSE')
	parser.add_argument('--json-output-name', help = 'JSON results: output filename', type = str, default = None)
	parser.add_argument('--json-target-system', help = 'JSON results: run target system', type = str, default = None)
	parser.add_argument('--json-use-compiler', help = 'JSON results: used compiler for building program', type = str, default = None)
	parser.add_argument('--json-build-type', help = 'JSON results: build type compiled and run program', type = str, default = None)
	parser.add_argument('--json-final-results', help = '(DEPRECATED) JSON results: calculation of coefficients for tests and output to JSON file (if activated) final test results, if necessary environment variables exist', type = str, default = 'FALSE')

	args = parser.parse_args()

	# Base arguments.
	base_program: str = os.path.abspath(args.program)
	base_suite: str = args.suite

	# Test setup.
	setup_check_output: bool = __t_or_f(args.check_output, "check-output")
	setup_timeout_factor: float = args.timeout_factor

	# JSON results.
	json_quick: bool = __t_or_f(args.json_quick, "json-quick")
	json_output_name: str = args.json_output_name
	json_target_system: str = args.json_target_system
	json_use_compiler: str = args.json_use_compiler
	json_build_type: str = args.json_build_type
	json_final_results: bool = __t_or_f(args.json_final_results, "json-final-results")

	if not json_quick:
		if not json_output_name is None and (json_target_system is None or json_use_compiler is None or json_build_type is None):
			print('usage: --json-output-name requires --json-target-system, --json-use-compiler and --json-build-type.')
			exit(1)

	task_select, coefficients = SELECTOR[base_suite]
	results = task_select.run(base_program, setup_check_output, setup_timeout_factor)
	exitcode = 0 if results.ok() else 1

	json_final_sum = __calculate_final_sum(results, coefficients)

	if not json_output_name is None or json_quick:
		json_full_dict: Dict[str, dict] = {}

		json_full_dict['target_system'] = json_target_system if not json_quick else 'Any target system'
		json_full_dict['use_compiler'] = json_use_compiler if not json_quick else 'Any use compiler'
		json_full_dict['build_type'] = json_build_type if not json_quick else 'Any build type'
		json_full_dict['passed'] = results.ok()
		json_full_dict['final_sum'] = json_final_sum
		json_full_dict['raw_results'] = results.get_raw_results()
		json_full_dict.update(results.json())

		json_object = json.dumps(json_full_dict, indent = 4)

		if json_output_name is None:
			json_output_name = __generate_unique_filename()

		with open(json_output_name, 'w') as file:
			file.write(json_object)

		print(f"-- JSON reported in {json_output_name}")

	exit(exitcode)

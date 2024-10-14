#!/usr/bin/env python3

import argparse
import os
import json

from typing import Dict, Tuple, Optional

import testsuites.base as base
import testsuites.sum as suite_sum

SELECTOR: Dict[str, Tuple[base.BaseTester, Optional[Dict[str, float]]]] = {
	'sum': suite_sum.get_instance()
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
	if coefficients is None:
		return None
	f_sum = 0.0
	raw_results = results.get_raw_results()
	for category, coefficient in coefficients.items():
		raw = raw_results[category]
		f_sum += coefficient * raw
	return f_sum

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--program', help = 'path to the program under test', type = str, required = True)
	parser.add_argument('--suite', help = 'select testing task', type = str, choices = SELECTOR, required = True)
	parser.add_argument('--check-output', help = 'is it necessary to check the program\'s output', type = str, default = 'TRUE')
	parser.add_argument('--timeout-factor', help = 'maximum execution time multiplier', type = float, default = 1.0)
	parser.add_argument('--json-output-name', help = 'JSON results: json output filename', type = str, default = None)
	parser.add_argument('--json-target-system', help = 'JSON results: json run target system', type = str, default = None)
	parser.add_argument('--json-use-compiler', help = 'JSON results: json used compiler for building program', type = str, default = None)
	parser.add_argument('--json-build-type', help = 'JSON results: json build type compiled and run program', type = str, default = None)
	parser.add_argument('--json-final-results', help = 'calculation of coefficients for tests and output to JSON file (if activated) final test results, if necessary environment variables exist', type = str, default = 'FALSE')

	args = parser.parse_args()

	# Base arguments.
	base_program: str = os.path.abspath(args.program)
	base_suite: str = args.suite

	# Test setup.
	setup_check_output: bool = __t_or_f(args.check_output, "check-output")
	setup_timeout_factor: float = args.timeout_factor

	# JSON results.
	json_output_name: str = args.json_output_name
	json_target_system: str = args.json_target_system
	json_use_compiler: str = args.json_use_compiler
	json_build_type: str = args.json_build_type
	json_final_results: bool = __t_or_f(args.json_final_results, "json-final-results")

	if not json_output_name is None and (json_target_system is None or json_use_compiler is None or json_build_type is None):
		print('usage: --json-output-name requires --json-target-system, --json-use-compiler and --json-build-type.')
		exit(1)

	task_select, coefficients = SELECTOR[base_suite]
	results = task_select.run(base_program, setup_check_output, setup_timeout_factor)
	exitcode = 0 if results.ok() else 1

	json_final_sum = __calculate_final_sum(results, coefficients)

	if not json_output_name is None:
		json_full_dict: Dict[str, dict] = {}

		json_full_dict['target_system'] = json_target_system
		json_full_dict['use_compiler'] = json_use_compiler
		json_full_dict['build_type'] = json_build_type
		json_full_dict['passed'] = results.ok()
		if json_final_sum is not None:
			json_full_dict['final_sum'] = json_final_sum
		json_full_dict['raw_results'] = results.get_raw_results()
		json_full_dict.update(results.json())

		json_object = json.dumps(json_full_dict, indent = 4)

		with open(json_output_name, 'w') as file:
			file.write(json_object)

	exit(exitcode)

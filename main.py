#!/usr/bin/env python3

import argparse
import os
import json

from typing import Dict

import testsuites.base as base
import testsuites.sum as suite_sum

SELECTOR: Dict[str, base.BaseTester] = {
	'sum': suite_sum.get_instance()
}

def t_or_f(arg: str) -> bool:
	ua = str(arg).upper()
	if ua == 'TRUE':
		return True
	elif ua == 'FALSE':
		return False
	else:
		print('usage: --check-output [True|False].')
		exit(1)

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

	args = parser.parse_args()

	# Base arguments.
	base_program: str = os.path.abspath(args.program)
	base_suite: str = args.suite

	# Test setup.
	setup_check_output: bool = t_or_f(args.check_output)
	setup_timeout_factor: float = args.timeout_factor

	# JSON results.
	json_output_name: str = args.json_output_name
	json_target_system: str = args.json_target_system
	json_use_compiler: str = args.json_use_compiler
	json_build_type: str = args.json_build_type

	if not json_output_name is None and (json_target_system is None or json_use_compiler is None or json_build_type is None):
		print('usage: --json-output-name requires --json-target-system, --json-use-compiler and --json-build-type.')
		exit(1)

	task_select = SELECTOR[base_suite]
	results = task_select.run(base_program, setup_check_output, setup_timeout_factor)
	exitcode = 0 if results.ok() else 1

	if not json_output_name is None:
		json_full_dict = {}

		json_full_dict['target_system'] = json_target_system
		json_full_dict['use_compiler'] = json_use_compiler
		json_full_dict['build_type'] = json_build_type
		json_full_dict['passed'] = results.ok()
		json_full_dict.update(results.json())

		json_object = json.dumps(json_full_dict, indent = 4)

		with open(json_output_name, 'w') as file:
			file.write(json_object)

	exit(exitcode)

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# Authors:
# - Paul Nilsson, paul.nilsson@cern.ch, 2025

import argparse
import os
import re
import shutil
import subprocess
from typing import Any

"""A tool to run code checking plugins on a source file or directory."""

# WARNING: this tools is in early development. Only the pylint test will work as expected.
# It should be possible to use is in a GitHub Action. The other tools are not yet fully implemented.


class CodeChecker:
    """A class to manage and run code checking plugins."""

    def __init__(self, verbose: bool = False, optional: Any = None, errorsonly: bool = False, select: str = None) -> None:
        """
        Initialize the CodeChecker with an optional verbosity setting.

        :param verbose: Whether to print detailed output (bool)
        :param optional: Optional parameter for compatibility with other plugins (Any).
        :param errorsonly: Whether to report only errors (bool)
        :param select: Select a particular error code to check for (str).
        """
        self.plugins: dict[str, type] = {}
        self.verbose = verbose
        self.optional = optional
        self.errorsonly = errorsonly
        self.select = select

    def register_plugin(self, name: str, plugin_module: type) -> None:
        """
        Register a plugin module with a given name.

        :param name: The name of the plugin (str)
        :param plugin_module: The plugin class (type).
        """
        self.plugins[name] = plugin_module

    def run_check(self, source: str, checker: str) -> tuple[int, str]:
        """
        Run the specified checker plugin on the given source.

        :param source: The source file or directory to check (str)
        :param checker: The name of the checker plugin to use (str)
        :return: The result of the check, exit code (int), messages (str).
        :raises ValueError: If the specified checker is not registered.
        """
        if checker in self.plugins:
            plugin = self.plugins[checker](verbose=self.verbose,
                                           optional=self.optional,
                                           errorsonly=self.errorsonly,
                                           select=self.select)
            return plugin.check(source)

        raise ValueError(f"Checker '{checker}' is not registered.")


class PylintPlugin:
    """A plugin to run pylint checks on a source file or directory."""

    def __init__(self, verbose: bool = False, optional: Any = None, errorsonly: bool = False, select: str = None) -> None:
        """
        Initialize the PylintPlugin with an optional verbosity setting.

        :param verbose: Whether to print detailed output (bool)
        :param optional: Optional parameter for compatibility with other plugins (Any)
        :param errorsonly: Whether to report only errors (bool)
        :param select: Select a particular error code to check for (str).
        """
        self.verbose = verbose
        self.optional = optional
        self.errorsonly = errorsonly
        self.select = select

    def get_source_files(self, source: str) -> list[str]:
        """
        Get a list of Python source files in the specified directory.

        :param source: The source file or directory to check.
        :return: A list of Python source files (list[str]).
        """
        if shutil.os.path.isdir(source):
            source_files = []
            for root, dirs, files in shutil.os.walk(source):
                for file in files:
                    if file.endswith(".py"):
                        source_files.append(os.path.join(root, file))
        else:
            source_files = [source]

        return source_files

    def get_command(self, filename: str) -> list:
        """
        Return the command to run pylint for the given filename.

        :param filename: The filename to check (str)
        :return: The command to run pylint (list).
        """
        cmd = ["pylint"]
        if self.errorsonly:
            cmd.append("--errors-only")
        cmd.append(filename)
        return cmd

    def find_pure_errors(self, stdout: str, errors: int) -> int:
        """
        Find and count pure errors in the pylint output.

        :param stdout: The pylint output (str)
        :param errors: The current error count (int)
        :return: The updated error count (int).
        """
        if stdout:
            for line in stdout.splitlines():
                if "*************" in line:
                    continue
                else:
                    errors += 1
                    print(f"{line}")

        return errors

    def get_scores(self, stdout: str, filename: str, scores: list, target_score: float, n_above_target: int,
                   current: int, total: int) -> tuple:
        """
        Extract the pylint score from the output and update the scores list.

        :param stdout: line stdout of the pylint command (std)
        :param filename: filename of the source file (str)
        :param scores: scores list (list)
        :param target_score: target score to compare against (float)
        :param n_above_target: score of at least the target score, typically 8.0 (int)
        :param current: current file number (int)
        :param total: total number of files (int)
        :return: scores list, n_above_target (tuple).
        """
        # for pylint, the optional parameter is used to set the target score
        score_match = re.search(r"Your code has been rated at ([0-9\.]+)/10", stdout)
        score = score_match.group(1) if score_match else "Score not found"
        if score != "Score not found":
            # only report scores less than the given number
            if target_score:
                if float(score) <= target_score:
                    # always print in this case
                    print(f"[{current}/{total}] {filename}: {score}")
                else:
                    # only print in verbose mode
                    if self.verbose:
                        print(f"[{current}/{total}] {filename}: {score}")
                    n_above_target += 1
                scores.append(score)
        else:
            if not target_score:
                print(f"[{current}/{total}] Score not found for {filename} (skipped)")

        return scores, n_above_target

    def check(self, source: str) -> tuple[int, str]:
        """
        Run pylint on the specified source and extract the pylint score.

        :param source: The source file or directory to check.
        :return: Exit code (int), the pylint output or score, based on verbosity (str).
        :raises EnvironmentError: If pylint is not available in the system's PATH.
        """
        if not shutil.which("pylint"):
            raise EnvironmentError("pylint is not available in the system's PATH")

        print(f"Running pylint checks on {source}...")

        if self.errorsonly:
            print("Running in errors-only mode")

        # If source is a directory, find all files with a .py extension
        source_files = self.get_source_files(source)

        def get_target_score(optional: str) -> float:
            try:
                if optional:
                    return float(optional)
                else:
                    return 10.0
            except ValueError as e:
                print(f"failed to convert {optional} to float: {e}")
                return 0.0

        scores = []
        target_score = get_target_score(self.optional)
        n_above_target = 0
        errors = 0

        # Run pylint and capture the output
        total = len(source_files)
        current = 1
        for filename in source_files:
            cmd = self.get_command(filename)
            result = subprocess.run(cmd, capture_output=True, text=True)
            if self.verbose:
                print(result.stdout)
                print(result.stderr)

            # Check for pure errors
            if self.errorsonly:
                errors = self.find_pure_errors(result.stdout, errors)
                continue

            # Extracting the pylint score using regex
            scores, n_above_target = self.get_scores(result.stdout, filename, scores, target_score, n_above_target, current, total)
            current += 1

        if scores:
            n_below_target = len(scores) - n_above_target
            exit_code = 1 if (n_below_target > 0 and target_score < 10) else 0
            if exit_code:
                print(f"Failed: found {n_below_target} files with a score less than target score {target_score}")
            average = round(sum(map(float, scores)) / len(scores), 2)
            message = (f"Average pylint score: {average}\n"
                       f"Number of files with a score of at least {target_score}: {n_above_target}\n"
                       f"Number of files with a score less than {target_score}: {n_below_target}\n"
                       f"Number of files processed: {len(scores)}")
            return exit_code, message
        else:
            exit_code = 1 if target_score > 0 else 0

        if self.errorsonly:
            return f"Number of errors: {errors}"

        return exit_code, result.stdout


class Flake8Plugin:
    """A plugin to run flake8 checks on a source file or directory."""

    def __init__(self, verbose: bool = False, optional: Any = None, errorsonly: bool = False, select: str = None) -> None:
        """
        Initialize the Flake8Plugin with an optional verbosity setting.

        :param verbose: Whether to print detailed output (bool)
        :param optional: Optional parameter for compatibility with other plugins (Any)
        :param errorsonly: Whether to report only errors (bool).
        :param select: Select a particular error code to check for (str).
        """
        self.verbose = verbose
        self.optional = optional
        self.errorsonly = errorsonly
        self.select = select

    def check(self, source: str) -> tuple[int, str]:
        """
        Run flake8 on the specified source.

        :param source: The source file or directory to check (str)
        :return: Exit code (int), the flake8 output (str).
        :raises EnvironmentError: If flake8 is not available in the system's PATH.
        """
        if not shutil.which("flake8"):
            raise EnvironmentError("flake8 is not available in the system's PATH")

        if self.verbose:
            print(f"Running flake8 checks on {source}...")

        cmd = ["flake8"]
        if self.select:
            cmd.extend(["--select", self.select, '--disable-noqa'])
        cmd.append(source)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if self.verbose:
            print(result.stdout)
            print(result.stderr)

        return 0, result.stdout if not self.verbose else None


class PyDocStylePlugin:
    """A plugin to run pydocstyle checks on a source file or directory."""

    def __init__(self, verbose: bool = False, optional: Any = None, errorsonly: bool = False, select: str = None) -> None:
        """
        Initialize the PyDocStylePlugin with an optional verbosity setting.

        :param verbose: Whether to print detailed output (bool)
        :param optional: Optional parameter for compatibility with other plugins (Any)
        :param errorsonly: Whether to report only errors (bool)
        :param select: Select a particular error code to check for (str).
        """
        self.verbose = verbose
        self.optional = optional
        self.errorsonly = errorsonly
        self.select = select

    def check(self, source: str) -> tuple[int, str]:
        """
        Run pydocstyle on the specified source.

        :param source: The source file or directory to check (str)
        :return: Exit code (int), the pydocstyle output (str).
        :raises EnvironmentError: If pydocstyle is not available in the system's PATH.
        """
        if not shutil.which("pydocstyle"):
            raise EnvironmentError("pydocstyle is not available in the system's PATH")

        if self.verbose:
            print(f"Running pydocstyle checks on {source}...")

        result = subprocess.run(["pydocstyle", source], capture_output=True, text=True)
        if self.verbose:
            print(result.stdout)
            print(result.stderr)

        return 0, result.stdout if not self.verbose else None


def main():
    """Parse arguments and run the code checker."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Code Checker Tool")
    parser.add_argument("-t", "--tool", choices=["pylint", "flake8", "pydocstyle"],
                        required=True, help="The code checker tool to use")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Increase output verbosity")
    parser.add_argument("-s", "--source", required=True,
                        help="The source file or directory to check")
    parser.add_argument("-S", "--scores-less-than", required=False,
                        help="Report scores less than given number (pylint only)")
    parser.add_argument("-E", "--errors-only", action="store_true", required=False,
                        help="Tool will only report pure errors")
    parser.add_argument("-c", "--select", required=False,
                        help="Select a particular error code to check for")
    args = parser.parse_args()

    # Create a CodeChecker instance and register plugins
    code_checker = CodeChecker(verbose=args.verbose,
                               optional=args.scores_less_than,
                               errorsonly=args.errors_only,
                               select=args.select)
    code_checker.register_plugin("pylint", PylintPlugin)
    code_checker.register_plugin("flake8", Flake8Plugin)
    code_checker.register_plugin("pydocstyle", PyDocStylePlugin)

    # Run the code checker
    try:
        exit_code, stdout = code_checker.run_check(args.source, args.tool)
    except (ValueError, EnvironmentError) as e:
        print(f"Error: {e}")
        exit_code = 1
    else:
        if stdout:
            print(stdout)

    if exit_code:
        print("Code check failed")
    else:
        print("Code check passed")

    exit(exit_code)


if __name__ == "__main__":
    """Run the main function."""
    main()

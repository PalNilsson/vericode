import argparse
import os
import re
import shutil
import subprocess
from typing import Optional, Any

"""A tool to run code checking plugins on a source file or directory."""


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

    def run_check(self, source: str, checker: str) -> Optional[str]:
        """
        Run the specified checker plugin on the given source.

        :param source: The source file or directory to check (str)
        :param checker: The name of the checker plugin to use (str)
        :return: The result of the check, if any (Optional[str])
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

    def get_scores(self, stdout: str, filename: str, scores: list, n_score_at_least: int,
                   current: int, total: int) -> tuple:
        """
        Extract the pylint score from the output and update the scores list.

        :param stdout: line stdout of the pylint command (std)
        :param filename: filename of the source file (str)
        :param scores: scores list (list)
        :param n_score_at_least: score of at least the target score, typically 8.0 (int)
        :param current: current file number (int)
        :param total: total number of files (int)
        :return: scores list, score_at_least (tuple).
        """
        # for pylint, the optional parameter is used to report scores less than the given number
        target_score = self.optional and isinstance(self.optional, str)
        score_match = re.search(r"Your code has been rated at ([0-9\.]+)/10", stdout)
        score = score_match.group(1) if score_match else "Score not found"
        if score != "Score not found":
            # only report scores less than the given number
            if target_score:
                if float(score) <= float(target_score):
                    print(f"[{current}/{total}] {filename}: {score}")
            else:  # normal processing
                print(f"[{current}/{total}] {filename}: {score}")
                if float(score) >= target_score:
                    n_score_at_least += 1
                scores.append(score)
        else:
            if not target_score:
                print(f"[{current}/{total}] Score not found for {filename} (skipped)")

        return scores, n_score_at_least

    def check(self, source: str) -> Optional[str]:
        """
        Run pylint on the specified source and extract the pylint score.

        :param source: The source file or directory to check.
        :return: The pylint output or score, based on verbosity.
        :raises EnvironmentError: If pylint is not available in the system's PATH.
        """
        if not shutil.which("pylint"):
            raise EnvironmentError("pylint is not available in the system's PATH")

        if self.verbose:
            print(f"Running pylint checks on {source}...")

        if self.errorsonly:
            print("Running in errors-only mode")

        # If source is a directory, find all files with a .py extension
        source_files = self.get_source_files(source)

        scores = []
        target_score = self.optional and isinstance(self.optional, str)
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
            scores, n_score_at_least = self.get_scores(result.stdout, filename, scores, n_score_at_least, current, total)
            current += 1

        if scores:
            average = round(sum(map(float, scores)) / len(scores), 2)
            message = (f"Average pylint score: {average}\n"
                       f"Number of files with a score of at least {target_score}: {n_score_at_least}\n"
                       f"Number of files processed: {len(scores)}")
            return message

        if self.errorsonly:
            return f"Number of errors: {errors}"

        return result.stdout


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

    def check(self, source: str) -> Optional[str]:
        """
        Run flake8 on the specified source.

        :param source: The source file or directory to check (str)
        :return: The flake8 output, if any (Optional[str]).
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

        return result.stdout if not self.verbose else None


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

    def check(self, source: str) -> Optional[str]:
        """
        Run pydocstyle on the specified source.

        :param source: The source file or directory to check (str)
        :return: The pydocstyle output, if any (Optional[str]).
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

        return result.stdout if not self.verbose else None


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
        stdout = code_checker.run_check(args.source, args.tool)
    except (ValueError, EnvironmentError) as e:
        print(f"Error: {e}")
    else:
        if stdout:
            print(stdout)


if __name__ == "__main__":
    """Run the main function."""
    main()

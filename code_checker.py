import argparse
import re
import shutil
import subprocess
from typing import Dict, Optional


class CodeChecker:
    """A class to manage and run code checking plugins."""

    def __init__(self, verbose: bool = False) -> None:
        """
        Initialize the CodeChecker with an optional verbosity setting.

        :param verbose: Whether to print detailed output (bool).
        """
        self.plugins: Dict[str, type] = {}
        self.verbose = verbose

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
            plugin = self.plugins[checker](self.verbose)
            return plugin.check(source)
        raise ValueError(f"Checker '{checker}' is not registered.")


class PylintPlugin:
    """A plugin to run pylint checks on a source file or directory."""

    def __init__(self, verbose: bool = False) -> None:
        """
        Initialize the PylintPlugin with an optional verbosity setting.

        :param verbose: Whether to print detailed output (bool).
        """
        self.verbose = verbose
        self.scorelimit = 8.0  # the score must be at least this number for the test to succeed

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

        # Run pylint and capture the output
        result = subprocess.run(["pylint", source], capture_output=True, text=True)
        if self.verbose:
            print(result.stdout)
            print(result.stderr)

        # Extracting the pylint score using regex
        score_match = re.search(r"Your code has been rated at ([0-9\.]+)/10", result.stdout)
        score = score_match.group(1) if score_match else "Score not found"
        print(f"Pylint Score: {score}")
        if float(score) < self.scorelimit:
            print("Pylint check failed.")
            return None

        return result.stdout


class Flake8Plugin:
    """A plugin to run flake8 checks on a source file or directory."""

    def __init__(self, verbose: bool = False) -> None:
        """
        Initialize the Flake8Plugin with an optional verbosity setting.

        :param verbose: Whether to print detailed output (bool).
        """
        self.verbose = verbose

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

        result = subprocess.run(["flake8", source], capture_output=True, text=True)
        if self.verbose:
            print(result.stdout)
            print(result.stderr)

        return result.stdout if not self.verbose else None


class PyDocStylePlugin:
    """A plugin to run pydocstyle checks on a source file or directory."""

    def __init__(self, verbose: bool = False) -> None:
        """
        Initialize the PyDocStylePlugin with an optional verbosity setting.

        :param verbose: Whether to print detailed output (bool).
        """
        self.verbose = verbose

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
    """Main function to parse arguments and run the code checker."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Code Checker Tool")
    parser.add_argument("-t", "--tool", choices=["pylint", "flake8", "pydocstyle"],
                        required=True, help="The code checker tool to use")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Increase output verbosity")
    parser.add_argument("-s", "--source", required=True,
                        help="The source file or directory to check")
    args = parser.parse_args()

    # Create a CodeChecker instance and register plugins
    code_checker = CodeChecker(verbose=args.verbose)
    code_checker.register_plugin("pylint", PylintPlugin)
    code_checker.register_plugin("flake8", Flake8Plugin)
    code_checker.register_plugin("pydocstyle", PyDocStylePlugin)

    # Run the code checker
    try:
        _ = code_checker.run_check(args.source, args.tool)
    except (ValueError, EnvironmentError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

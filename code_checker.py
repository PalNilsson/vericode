import argparse
import re
import subprocess


class CodeChecker:
    def __init__(self, verbose=False):
        self.plugins = {}
        self.verbose = verbose

    def register_plugin(self, name, plugin_module):
        self.plugins[name] = plugin_module

    def run_check(self, source, checker):
        if checker in self.plugins:
            plugin = self.plugins[checker](self.verbose)
            return plugin.check(source)
        raise ValueError(f"Checker '{checker}' is not registered.")


class PylintPlugin:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.scorelimit = 8.0  # the score must be at least this number for the test to succeed

    def check(self, source):
        if self.verbose:
            print(f"Running pylint checks on {source}...")
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
    def __init__(self, verbose=False):
        self.verbose = verbose

    def check(self, source):
        if self.verbose:
            print(f"Running flake8 checks on {source}...")
        result = subprocess.run(["flake8", source], capture_output=True, text=True)
        if self.verbose:
            print(result.stdout)
            print(result.stderr)
        return result.stdout if not self.verbose else None


class PyDocStylePlugin:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def check(self, source):
        if self.verbose:
            print(f"Running pydocstyle checks on {source}...")
        result = subprocess.run(["pydocstyle", source], capture_output=True, text=True)
        if self.verbose:
            print(result.stdout)
            print(result.stderr)
        return result.stdout if not self.verbose else None


def main():
    parser = argparse.ArgumentParser(description="Code Checker Tool")
    parser.add_argument("-t", "--tool", choices=["pylint", "flake8", "pydocstyle"],
                        required=True, help="The code checker tool to use")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Increase output verbosity")
    parser.add_argument("-s", "--source", required=True,
                        help="The source file or directory to check")
    args = parser.parse_args()

    code_checker = CodeChecker(verbose=args.verbose)

    code_checker.register_plugin("pylint", PylintPlugin)
    code_checker.register_plugin("flake8", Flake8Plugin)
    code_checker.register_plugin("pydocstyle", PyDocStylePlugin)

    _ = code_checker.run_check(args.source, args.tool)


if __name__ == "__main__":
    main()

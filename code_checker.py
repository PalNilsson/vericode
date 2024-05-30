import argparse
import subprocess


class CodeChecker:
    def __init__(self, verbose=False):
        self.plugins = {}
        self.verbose = verbose

    def register_plugin(self, name, plugin_module):
        self.plugins[name] = plugin_module

    def run_check(self, directory, checker):
        if checker in self.plugins:
            plugin = self.plugins[checker](self.verbose)
            return plugin.check(directory)
        else:
            raise ValueError(f"Checker '{checker}' is not registered.")


class PylintPlugin:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def check(self, directory):
        if self.verbose:
            print(f"Running pylint checks on {directory}...")
        result = subprocess.run(["pylint", directory], capture_output=True, text=True)
        if self.verbose:
            print(result.stdout)
            print(result.stderr)
        return result.stdout if not self.verbose else None


class Flake8Plugin:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def check(self, directory):
        if self.verbose:
            print(f"Running flake8 checks on {directory}...")
        result = subprocess.run(["flake8", directory], capture_output=True, text=True)
        if self.verbose:
            print(result.stdout)
            print(result.stderr)
        return result.stdout if not self.verbose else None


class PyDocStylePlugin:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def check(self, directory):
        if self.verbose:
            print(f"Running pydocstyle checks on {directory}...")
        result = subprocess.run(["pydocstyle", directory], capture_output=True, text=True)
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
    parser.add_argument("-d", "--directory", required=True,
                        help="The directory of the code to check")
    args = parser.parse_args()

    code_checker = CodeChecker(verbose=args.verbose)

    code_checker.register_plugin("pylint", PylintPlugin)
    code_checker.register_plugin("flake8", Flake8Plugin)
    code_checker.register_plugin("pydocstyle", PyDocStylePlugin)

    result = code_checker.run_check(args.directory, args.tool)
    if result:
        print(result)


if __name__ == "__main__":
    main()

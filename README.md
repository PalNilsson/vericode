# codechecker
Plugin based python3 tool that to be used with code checkers. The tool currently has plugins for pylint, flake8 and
pydocstyle.

# How to use
The tool can be used by running the following command:

<code>python3 code_checker.py -t &lt;tool&gt; -s &lt;source&gt;</code>

# Example

Standard flake8 test of the code in the given directory:
<code>python3 code_checker.py -t flake8 -s <i>directory</i></code>

Standard pylint test of the code in the given directory:
<code>python3 code_checker.py -t pylint -s <i>directory</i></code>

Pure pylint error reporting:
<code>python3 code_checker.py -E -t pylint -s <i>directory</i></code>


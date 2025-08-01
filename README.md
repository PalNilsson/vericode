# VeriCode
A plugin-based python tool that to be used with various code checkers. The tool currently has plugins for pylint, flake8 and
pydocstyle. It will have support for TypeScript in the future.

# How to use
The tool can be used by running the following command:

<code>python3 vericode.py -t &lt;tool&gt; -s &lt;source&gt;</code>

# Examples

Standard flake8 test of the code in the given directory:

<code>python3 vericode.py -t flake8 -s <i>directory or file</i></code>

Only report files that have a certain flake8 error:

<code>python3 vericode.py --select <i>error_code</i> -t flake8 -s <i>directory or file</i></code>

Standard pylint test of the code in the given directory. In this mode, the tool reports processed files, their individual
pylint scores and the average score for the directory:

<code>python3 vericode.py -t pylint -s <i>directory or file</i></code>

Pure pylint error reporting:

<code>python3 vericode.py --errors-only -t pylint -s <i>directory or file</i></code>

Only report files that have a pylint score below a certain threshold:

<code>python3 vericode.py --scores-less-than <i>threshold</i> -t pylint -s <i>directory or file</i></code>

In the case there are such files, the tool will print them out and consider the run failed.

Standard pydocstyle test of the code in the given directory:

<code>python3 vericode.py -t pydocstyle -s <i>directory or file</i></code>

# Limitations

* Only one directory or file can be processed at a time. If a directory is given, the tool will process all
files in the directory and its subdirectories.
* --select flag is only supported for flake8 tests.


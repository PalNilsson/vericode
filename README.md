# VeriCode
A plugin-based python tool that to be used with various code checkers. The tool currently has plugins for pylint, flake8 and
pydocstyle. It will have support for TypeScript in the future.

# Installation

The tool can be pip installed:

```
pip install vericode
```

# How to use
The tool is run from the command line. It requires a tool to be specified with the `-t` flag and a source directory or file
to be checked with the `-s` flag. The tool will run the specified code checker on the given source and report the results. The tool can also be configured with various flags to control
the output and behavior. See examples below.

<code>vericode -t &lt;tool&gt; -s &lt;source&gt;</code>

# Examples

Standard flake8 test of the code in the given directory:

<code>vericode -t flake8 -s <i>directory or file</i></code>

Only report files that have a certain flake8 error:

<code>vericode --select <i>error_code</i> -t flake8 -s <i>directory or file</i></code>

Standard pylint test of the code in the given directory. In this mode, the tool reports processed files, their individual
pylint scores and the average score for the directory:

<code>vericode -t pylint -s <i>directory or file</i></code>

Pure pylint error reporting:

<code>vericode --errors-only -t pylint -s <i>directory or file</i></code>

Only report files that have a pylint score below a certain threshold:

<code>vericode --scores-less-than <i>threshold</i> -t pylint -s <i>directory or file</i></code>

In the case there are such files, the tool will print them out and consider the run failed.

Standard pydocstyle test of the code in the given directory:

<code>vericode -t pydocstyle -s <i>directory or file</i></code>

# Limitations

* Only one directory or file can be processed at a time. If a directory is given, the tool will process all
files in the directory and its subdirectories.
* --select flag is only supported for flake8 tests.

WARNING: The tool is still in development and may have bugs. If you find any, please report them on the GitHub repository.

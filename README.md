# code-quality-checks
Tool to run various code quality checks on a Git repository

This Python script can run tools to format and check C++ and Python code.
It only processes files which changed from some customisable reference commit.

It is typically necessary to use `--prefix=1` to strip the `a/` and `b/` prefixes prepended to file paths by `git diff`.

This tool was heavily influenced by `clang-format-diff.py` distributed as part of LLVM.

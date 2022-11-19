import argparse
import pathlib
import sys
import textwrap
from typing import Optional


def main(args: Optional[list[str]] = None) -> None:
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--basedir", type=pathlib.Path, required=True)
        parser.add_argument("--path", type=pathlib.Path, required=True)
        parser.add_argument("--output", type=pathlib.Path, required=True)
        parsed = parser.parse_args(args)

        path: pathlib.Path = parsed.path
        basedir: pathlib.Path = parsed.basedir
        output: pathlib.Path = parsed.output
        code = textwrap.dedent(
            f"""\
            #!{sys.executable}
            \"\"\"This is a helper script to run the target Python code.

            We need this script to set PYTHONPATH portably. The env command, quoting something, etc. are not portable or difficult to implement.
            \"\"\"

            import os
            import sys

            # arguments
            path = {repr(str(path.resolve()))}
            basedir = {repr(str(basedir.resolve()))}

            # run {str(path)}
            env = dict(os.environ)
            if "PYTHONPATH" in env:
                env["PYTHONPATH"] = basedir + os.pathsep + env["PYTHONPATH"]
            else:
                env["PYTHONPATH"] = basedir  # set `PYTHONPATH` to import files relative to the root directory
            os.execve(sys.executable, [sys.executable, path], env=env)  # use `os.execve` to avoid making an unnecessary parent process
        """
        )
        output.write_text(code, encoding="utf-8")
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(2)


if __name__ == "__main__":
    main()

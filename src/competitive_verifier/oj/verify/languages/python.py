# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false
# Python Version: 3.x
import concurrent.futures
import functools
import os
import pathlib
import platform
import sys
from logging import getLogger
from typing import Sequence

import importlab.environment
import importlab.fs
import importlab.graph

from competitive_verifier.oj.verify.models import Language, LanguageEnvironment

logger = getLogger(__name__)


class PythonLanguageEnvironment(LanguageEnvironment):
    @property
    def name(self) -> str:
        return "Python"

    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        python_path = os.getenv("PYTHONPATH")
        if python_path:
            python_path = basedir.resolve().as_posix() + os.pathsep + python_path
        else:
            python_path = basedir.resolve().as_posix()
        return f"env PYTHONPATH={python_path} python {path}"


@functools.lru_cache(maxsize=None)
def _python_list_depending_files(
    path: pathlib.Path, basedir: pathlib.Path
) -> list[pathlib.Path]:
    # compute the dependency graph of the `path`
    env = importlab.environment.Environment(
        importlab.fs.Path([importlab.fs.OSFileSystem(str(basedir.resolve()))]),
        (sys.version_info.major, sys.version_info.minor),
    )
    try:
        executor = concurrent.futures.ThreadPoolExecutor()
        future = executor.submit(
            importlab.graph.ImportGraph.create,  # pyright: ignore[reportUnknownArgumentType]
            env,
            [str(path)],
            True,
        )
        if platform.uname().system == "Windows":
            timeout = 5.0  # 1.0 sec causes timeout on CI using Windows
        else:
            timeout = 1.0
        res_graph = future.result(timeout=timeout)
    except concurrent.futures.TimeoutError as e:
        raise RuntimeError(
            f"Failed to analyze the dependency graph (timeout): {path}"
        ) from e
    try:
        node_deps_pairs: list[tuple[str, list[str]]] = res_graph.deps_list()
    except Exception as e:
        raise RuntimeError(
            f"Failed to analyze the dependency graph (circular imports?): {path}"
        ) from e
    logger.debug("the dependency graph of %s: %s", str(path), node_deps_pairs)

    # collect Python files which are depended by the `path` and under `basedir`
    res_deps: list[pathlib.Path] = []
    res_deps.append(path.resolve())
    for node_, deps_ in node_deps_pairs:
        node = pathlib.Path(node_)
        deps = list(map(pathlib.Path, deps_))
        if node.resolve() == path.resolve():
            for dep in deps:
                if basedir.resolve() in dep.resolve().parents:
                    res_deps.append(dep.resolve())
            break
    return list(set(res_deps))


class PythonLanguage(Language):
    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        return _python_list_depending_files(path.resolve(), basedir)

    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> Sequence[PythonLanguageEnvironment]:
        return [PythonLanguageEnvironment()]

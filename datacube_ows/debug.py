from __future__ import annotations

import os

TYPE_CHECKING = False
if TYPE_CHECKING:
    from logging import Logger


def initialise_debugging(log: Logger | None = None) -> None:
    # PYCHARM Debugging
    dbg = os.environ.get("PYDEV_DEBUG")
    if dbg and dbg.lower() not in ("no", "false", "f", "n"):
        import pydevd_pycharm

        pydevd_pycharm.settrace(
            "172.17.0.1", port=12321, stdout_to_server=True, stderr_to_server=True
        )
        if log:
            log.info("PyCharm Debugging enabled")

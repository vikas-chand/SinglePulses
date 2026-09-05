"""Sandbox-only log redirect for the Codex 20-burst producer campaign.

The managed workspace cannot append to threeML/astromodels' default log
directories under the user's home.  Intercept only those two paths and leave
all other ``Path.expanduser`` calls unchanged.
"""

import os
from pathlib import Path


_ORIGINAL_EXPANDUSER = Path.expanduser
_LOG_REDIRECTS = {
    "~/.astromodels/log": Path("/private/tmp/codex_campaign20_threeml_logs"),
    "~/.threeml/log": Path("/private/tmp/codex_campaign20_threeml_logs"),
}


def _campaign_expanduser(path):
    redirected = _LOG_REDIRECTS.get(str(path))
    if redirected is not None:
        redirected.mkdir(parents=True, exist_ok=True)
        return redirected
    return _ORIGINAL_EXPANDUSER(path)


Path.expanduser = _campaign_expanduser


# The managed sandbox denies the SC_SEM_NSEMS_MAX query made by
# ProcessPoolExecutor in both campaign Python environments.  The canonical
# upstream MVT code constructs that executor even for one worker.  Enable this
# transport-only substitution explicitly for those invocations; estimator
# functions, inputs, task order, and the requested one-worker concurrency are
# unchanged.  It is intentionally off for every ordinary campaign command.
if os.environ.get("CODEX_CAMPAIGN20_THREAD_EXECUTOR") == "1":
    import concurrent.futures as _concurrent_futures

    _concurrent_futures.ProcessPoolExecutor = (
        _concurrent_futures.ThreadPoolExecutor
    )

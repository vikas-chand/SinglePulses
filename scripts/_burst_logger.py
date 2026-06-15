"""
Per-burst, per-run analysis logger — mirrors gtburst's `gtburst.log` style
(ConsoleText.py:57) but timestamps each file so no previous log is ever
overwritten.

Path:  results/per_burst/<trigger>/logs/<script>_<UTC_timestamp>.log
Mode:  'w' on a unique timestamped path → always a fresh file.
Header/footer style:
  Analysis started at YYYY-MM-DD HH:MM:SS by user USER
  ...
  Analysis ended at YYYY-MM-DD HH:MM:SS

Tees sys.stdout AND sys.stderr to both the terminal and the log file
(line-buffered, flushed on every write).

Usage:
    from _burst_logger import BurstLogger
    with BurstLogger(trigger='bn260105973', script='10_spectral_fit_burst',
                     base='/path/to/results/per_burst'):
        main()
"""
import os, sys, getpass
from datetime import datetime, timezone


class _Tee:
    """Write to multiple file-like targets; flush on every write."""
    def __init__(self, *targets):
        self.targets = targets
    def write(self, s):
        for t in self.targets:
            try:
                t.write(s); t.flush()
            except Exception:
                pass
    def flush(self):
        for t in self.targets:
            try: t.flush()
            except Exception: pass
    def isatty(self):
        # Some libs check isatty; report False so they don't ANSI-colour the log
        return False


class BurstLogger:
    def __init__(self, trigger, script, base):
        self.trigger = trigger
        self.script = script
        self.base = base
        self.logfile = None
        self.path = None
        self._orig_stdout = None
        self._orig_stderr = None

    def __enter__(self):
        log_dir = os.path.join(self.base, self.trigger, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        self.path = os.path.join(log_dir, f'{self.script}_{stamp}.log')
        # 'x' = exclusive create → guarantees we never overwrite even
        # if two runs collide on the same second.
        i = 0
        while True:
            try:
                self.logfile = open(self.path, 'x')
                break
            except FileExistsError:
                i += 1
                self.path = os.path.join(log_dir, f'{self.script}_{stamp}_{i}.log')

        ltime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username = getpass.getuser()
        self.logfile.write(
            f'Analysis started at {ltime} by user {username}\n'
            f'Trigger: {self.trigger}\n'
            f'Script:  {self.script}\n'
            f'Argv:    {" ".join(sys.argv)}\n'
            f'CWD:     {os.getcwd()}\n'
            f'PID:     {os.getpid()}\n'
            f'{"=" * 72}\n\n')
        self.logfile.flush()

        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        sys.stdout = _Tee(self._orig_stdout, self.logfile)
        sys.stderr = _Tee(self._orig_stderr, self.logfile)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ltime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            if exc_type is not None:
                self.logfile.write(
                    f'\n\nFATAL: {exc_type.__name__}: {exc_val}\n')
            self.logfile.write(f'\n\nAnalysis ended at {ltime}\n')
            self.logfile.flush()
            self.logfile.close()
        finally:
            sys.stdout = self._orig_stdout
            sys.stderr = self._orig_stderr
        # Don't swallow the exception
        return False

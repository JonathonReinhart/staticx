#!/usr/bin/env python3
import argparse
import os
import io
from pathlib import Path
import selectors
import signal
import subprocess
import time

MY_DIR = Path(__file__).parent.absolute()
TEST_APP_PATH = MY_DIR / "build/app"

FORBIDDEN_SIGNALS = {
    signal.SIGKILL,
    signal.SIGSTOP,
}

TEST_SIGNALS = [
    signal.SIGHUP,
    signal.SIGINT,
    signal.SIGQUIT,
    #signal.SIGILL,
    #signal.SIGTRAP,
    #signal.SIGABRT,
    #signal.SIGBUS,
    #signal.SIGFPE,
    #signal.SIGKILL,
    signal.SIGUSR1,
    #signal.SIGSEGV,
    signal.SIGUSR2,
    signal.SIGPIPE,
    #signal.SIGALRM,
    signal.SIGTERM,
    #signal.SIGSTKFLT,  # 16
    #signal.SIGCHLD,
    signal.SIGCONT,
    #signal.SIGSTOP,  # can't be caught
    signal.SIGTSTP,
    #signal.SIGTTIN,  # ?
    #signal.SIGTTOU,  # ?
    #signal.SIGURG,  # ?
    #signal.SIGXCPU,  # ?
    #signal.SIGXFSZ,  # ?
    #signal.SIGVTALRM,  # ?
    #signal.SIGPROF,  # ?
    #signal.SIGIO,  # ?
    #signal.SIGPWR,  # ?
    #signal.SIGSYS,  # ?
] + list(range(signal.SIGRTMIN, signal.SIGRTMAX+1))

DEFAULT_TIMEOUT = 1.0

class TestApp:
    def __init__(self, path):
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            #text=True,
        )

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        if self.proc:
            self.close()

    def close(self):
        stopped = False

        # First try to stop the app the nice way: close stdin
        if not stopped:
            print(f"Stopping pid {self.pid} gracefully")
            self.proc.stdin.close()
            try:
                self.proc.wait(1)
                stopped = True
            except subprocess.TimeoutExpired:
                pass

        # Now the hard way: SIGKILL
        if not stopped:
            print(f"Killing pid {self.pid} with fire")
            self.proc.kill()
            self.proc.wait(1)

        self.proc = None

    @property
    def pid(self):
        return self.proc.pid

    def getline(self, timeout=DEFAULT_TIMEOUT):
        # requires setlinebuf() in the C app!
        return read_line(self.proc.stdout, timeout=timeout).strip()

    def wait_for_ready(self):
        try:
            line = self.getline()
        except TimeoutError:
            raise TimeoutError("Timed out waiting for ready")

        assert line == "ready"

    def test_signal(self, signum):
        if signum in FORBIDDEN_SIGNALS:
            raise ValueError(f"Forbidden signal: {signum}")

        self.proc.send_signal(signum)

        try:
            line = self.getline()
        except TimeoutError:
            raise TimeoutError(f"Timed out waiting for report for signal {signum}")

        parts = line.split()
        assert parts[0] == "signal"
        recv_signum = int(parts[1])

        assert recv_signum == signum




def read_line(f, timeout=None):
    if isinstance(f, io.BufferedReader):
        f = f.raw
    else:
        raise ValueError("What are we even doing anymore?")

    if not isinstance(timeout, Timeout):
        timeout = Timeout(timeout)

    sel = selectors.DefaultSelector()
    sel.register(f, selectors.EVENT_READ)

    data = b""
    while not timeout.expired:
        events = sel.select(timeout.remain)
        if not events:
            break

        # assume readable
        c = f.read(1)
        if not c:
            raise EOFError()
        data += c
        if c == b"\n":
            return data.decode()

    raise TimeoutError()


class Timeout:
    def __init__(self, timeout=None):
        self.timeout = timeout
        self.start = time.time()

    def __repr__(self):
        return f"Timeout(timeout={self.timeout}): elepsed={self.elapsed} remain={self.remain} expired={self.expired}"

    @property
    def elapsed(self):
        return time.time() - self.start

    @property
    def remain(self):
        if self.timeout is None:
            return None  # infinite, compatible with select()
        return max(0, self.timeout - self.elapsed)

    @property
    def expired(self):
        if self.timeout is None:
            return False
        return self.elapsed >= self.timeout


def valid_path(access=os.R_OK):
    def convert(s):
        path = Path(s)
        if not path.is_file():
            raise argparse.ArgumentTypeError(f"Not a file: {s}")
        if not os.access(path, access):
            checks = []
            if access & os.R_OK:
                checks.append("readable")
            if access & os.W_OK:
                checks.append("writeable")
            if access & os.X_OK:
                checks.append("executable")
            checks_str = "+".join(checks)
            raise argparse.ArgumentTypeError(f"File not {checks_str}: {s}")
        return path

    return convert


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("program", type=valid_path(os.R_OK | os.X_OK))
    return parser.parse_args()


def main():
    args = parse_args()

    proc = TestApp(args.program)
    with proc:
        print(f"Started {proc.pid}")

        proc.wait_for_ready()
        for signum in TEST_SIGNALS:
            print(f"Testing signal {signum}")
            proc.test_signal(signum)


if __name__ == "__main__":
    main()

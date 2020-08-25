import abc
import atexit
import os
import sys
import time
from signal import SIGTERM
from typing import NoReturn
from typing import Optional


class Daemon(abc.ABC):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(
        self,
        pidfile: str,
        stdin: str = "/dev/null",
        stdout: str = "/dev/null",
        stderr: str = "/dev/null",
    ) -> None:
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def _daemonize(self) -> Optional[NoReturn]:
        """
        Do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                print("First parent exiting...")
                sys.exit(0)
        except OSError as e:
            print(f"fork #1 failed: {e.errno} {(e.strerror)}", file=sys.stderr)
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                print("Second parent exiting...")
                sys.exit(0)
        except OSError as e:
            print(f"fork #2 failed: {e.errno} ({e.strerror})", file=sys.stderr)
            sys.exit(1)

        pid = os.getpid()
        print(f"Successfully double-forked with pid {pid}. Now detaching...")

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull)
        so = open(os.devnull, "a+")
        se = open(os.devnull, "a+")
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self._delpid)
        with open(self.pidfile, "w+") as f:
            f.write(f"{pid}\n")

        return None

    def _delpid(self) -> None:
        os.remove(self.pidfile)

    def start(self) -> int:
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        pid: Optional[int] = None
        try:
            pf = open(self.pidfile)
            pid = int(pf.read().strip())
            pf.close()
        except OSError:
            pass

        if pid:
            print(
                f"pidfile {self.pidfile} already exists with pid {pid}. "
                "Daemon already running?",
                file=sys.stderr,
            )
            return 1

        # Start the daemon
        self._daemonize()
        self.run()
        return 0

    def stop(self) -> int:
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        pid: Optional[int] = None
        try:
            pf = open(self.pidfile)
            pid = int(pf.read().strip())
            pf.close()
        except OSError:
            pass

        if not pid:
            print(
                f"pidfile {self.pidfile} does not exist. Daemon not running?\n",
                file=sys.stderr,
            )
            return 0  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            if str(err).find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(err, file=sys.stderr)
                return 1
        return 0

    def restart(self) -> int:
        """
        Restart the daemon
        """
        if rc := self.stop():
            return rc
        if rc := self.start():
            return rc
        return 0

    @abc.abstractmethod
    def run(self) -> int:
        """
        You should override this method when you subclass Daemon. It will be
        called after the process has been daemonized by start() or restart().
        """

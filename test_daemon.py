#!/usr/bin/env python3
import argparse
import sys
import time

from daemon import Daemon


class MyDaemon(Daemon):
    def run(self) -> int:
        while True:
            time.sleep(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "stop", "restart"))
    args = parser.parse_args()

    daemon = MyDaemon("/tmp/daemon-example.pid")
    if args.action == "start":
        return daemon.start()
    if args.action == "stop":
        return daemon.stop()
    if args.action == "restart":
        return daemon.restart()
    raise NotImplementedError(f"No case for '{args.action}'")


if __name__ == "__main__":
    sys.exit(main())

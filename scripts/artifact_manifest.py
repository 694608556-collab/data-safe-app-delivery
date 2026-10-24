#!/usr/bin/env python3
"""Read explicit regular files and emit identity evidence; never install or upload.

Python 3.9+, standard library only. No package internals or signing verification.
The manifest may contain private paths. Keep it local unless sanitized.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

READ_BYTES = 1024 * 1024


def _signature(info):
    # Windows path-stat and descriptor-stat expose different ctime semantics in
    # some Python versions; compare portable identity, size, mtime and type.
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            stat.S_IFMT(info.st_mode))


def fingerprint(filename):
    """Hash a stable regular file in bounded memory, rejecting observed changes."""
    path = Path(filename).expanduser().absolute()
    initial = path.lstat()
    if stat.S_ISLNK(initial.st_mode) or not stat.S_ISREG(initial.st_mode):
        raise ValueError("Only explicit regular files are accepted: " + str(path))
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if _signature(initial) != _signature(opened):
            raise ValueError("File changed before reading: " + str(path))
        while True:
            block = stream.read(READ_BYTES)
            if not block:
                break
            digest.update(block)
            count += len(block)
        finished = os.fstat(stream.fileno())
    current = path.lstat()
    if (count != opened.st_size or _signature(opened) != _signature(finished)
            or _signature(finished) != _signature(current)):
        raise ValueError("File changed while reading: " + str(path))
    return {
        "path": str(path),
        "bytes": count,
        "sha256": digest.hexdigest(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="Explicit files, use -- before names")
    args = parser.parse_args(argv)
    try:
        # Finish every read before emitting JSON; failures never emit partial success.
        records = [fingerprint(filename) for filename in args.files]
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps({
        "schemaVersion": 1,
        "evidenceType": "file-identity-only",
        "artifacts": records,
    }, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

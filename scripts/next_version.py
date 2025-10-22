#!/usr/bin/env python3

import datetime
import os
import re
import string
import subprocess
import sys


TAG_PREFIX = "v"


def current_yy_q(dt: datetime.datetime):
    yy = dt.strftime("%y")
    month = dt.month
    if month <= 3:
        q = 1
    elif month <= 6:
        q = 2
    elif month <= 9:
        q = 3
    else:
        q = 4
    return yy, q


def letters_to_num(s: str) -> int:
    # Excel-like base-26: a->1, z->26, aa->27
    n = 0
    for ch in s:
        if ch not in string.ascii_lowercase:
            raise ValueError(f"Invalid patch letter: {ch}")
        n = n * 26 + (ord(ch) - 96)
    return n


def num_to_letters(n: int) -> str:
    # Inverse of letters_to_num
    if n <= 0:
        raise ValueError("n must be positive")
    res = []
    while n > 0:
        n -= 1
        res.append(chr((n % 26) + 97))
        n //= 26
    return "".join(reversed(res))


def get_existing_patches(yy: str, q: int) -> list[str]:
    pattern = f"{TAG_PREFIX}{yy}.{q}."
    try:
        out = subprocess.check_output(["git", "tag", "--list", f"{pattern}*"]).decode().strip()
    except subprocess.CalledProcessError:
        out = ""
    tags = [t for t in out.splitlines() if t]

    patches = []
    rx = re.compile(rf"^{re.escape(TAG_PREFIX)}{yy}\.{q}\.([a-z]+)$")
    for t in tags:
        m = rx.match(t)
        if m:
            patches.append(m.group(1))
    return patches


def compute_next_version(now: datetime.datetime | None = None) -> str:
    if now is None:
        now = datetime.datetime.utcnow()
    yy, q = current_yy_q(now)
    patches = get_existing_patches(yy, q)
    if not patches:
        patch_letters = "a"
    else:
        max_num = max(letters_to_num(p) for p in patches)
        patch_letters = num_to_letters(max_num + 1)
    return f"{TAG_PREFIX}{yy}.{q}.{patch_letters}"


def main() -> int:
    version = compute_next_version()
    
    # Print version for capture in workflows and build scripts
    # No longer writes VERSION file - version passed via HUGO_VERSION_TAG env var
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


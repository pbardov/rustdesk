#!/usr/bin/env python3
"""Collect platform packages under unambiguous VSGSoft distribution names."""

import argparse
import os
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("platform", choices=["windows", "linux", "macos"])
    parser.add_argument("arch")
    args = parser.parse_args()
    version = os.environ["VERSION"]
    base = f"rustdesk-vsgsoft-{version}-{args.platform}-{args.arch}"
    dist = Path("dist")
    dist.mkdir(exist_ok=True)
    if args.platform == "windows":
        sources = [(Path(f"SignOutput/rustdesk-{version}-{args.arch}.{ext}"), f"{base}.{ext}") for ext in ["exe", "msi"]]
    elif args.platform == "macos":
        sources = [(Path(f"rustdesk-{version}-{args.arch}.dmg"), f"{base}.dmg")]
    else:
        sources = [(Path(f"rustdesk-{version}-{args.arch}.deb"), f"{base}.deb")]
        sources += [(p, base + ("-suse" if "suse" in p.stem else "") + ".rpm") for p in sorted(Path(".").glob(f"rustdesk-{version}*.rpm"))]
        if not any(p.suffix == ".rpm" for p, _ in sources):
            raise RuntimeError("No RPM was built")
    for source, name in sources:
        if not source.is_file() or source.stat().st_size < 100_000:
            raise RuntimeError(f"Missing or empty build output: {source}")
        shutil.copy2(source, dist / name)
        print("Package:", dist / name)


if __name__ == "__main__":
    main()

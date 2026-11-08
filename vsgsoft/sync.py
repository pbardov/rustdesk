#!/usr/bin/env python3
"""Synchronize the custom branch with the latest stable upstream release."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def main():
    root = Path.cwd()
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ["GITHUB_REF_NAME"]
    if branch != "vsgsoft":
        raise RuntimeError("The sync workflow must run from the vsgsoft branch")
    release = json.loads(output("gh", "api", "repos/rustdesk/rustdesk/releases/latest"))
    version = release["tag_name"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"Unexpected stable release tag: {version}")
    run(
        "git", "fetch", "--no-tags", "--depth=1",
        "https://github.com/rustdesk/rustdesk.git", f"refs/tags/{version}",
    )
    upstream = output("git", "rev-parse", "FETCH_HEAD^{commit}")
    # Keep the fork's automation while replacing application sources with the release tree.
    with tempfile.TemporaryDirectory() as folder:
        saved = Path(folder)
        for name in ["vsgsoft", ".github/workflows", "VSGSOFT.md"]:
            src = root / name
            dst = saved / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(src, dst)
        run("git", "read-tree", "--reset", "-u", upstream)
        for name in ["vsgsoft", ".github/workflows", "VSGSOFT.md"]:
            dst = root / name
            if dst.is_dir():
                shutil.rmtree(dst)
            elif dst.exists():
                dst.unlink()
            src = saved / name
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
    run("python3", "vsgsoft/configure.py")
    digest = hashlib.sha256()
    for path in sorted([*Path("vsgsoft").glob("*.py"), Path("vsgsoft/server.json"), *Path(".github/workflows").glob("*.yml")]):
        digest.update(str(path).encode())
        digest.update(path.read_bytes())
    customization = digest.hexdigest()[:10]
    metadata = {
        "repository": "rustdesk/rustdesk",
        "tag": version,
        "commit": upstream,
        "customization": customization,
    }
    Path("vsgsoft/upstream.json").write_text(json.dumps(metadata, indent=2) + "\n")
    run("git", "config", "user.name", "Pavel Bardov")
    run("git", "config", "user.email", "pbardov@gmail.com")
    run("git", "add", "--all")
    changed = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode
    if changed not in [0, 1]:
        raise RuntimeError("Cannot inspect source changes")
    if changed:
        run("git", "commit", "-m", f"Sync RustDesk {version} with VSGSoft server defaults")
        run("git", "push", "origin", f"HEAD:refs/heads/{branch}")
    source = output("git", "rev-parse", "HEAD")
    tag = f"vsgsoft-{version}-{customization}"
    if os.environ.get("FORCE_REBUILD") == "true":
        tag += "-r" + os.environ["GITHUB_RUN_NUMBER"]
    existing = subprocess.run(
        ["gh", "api", f"repos/{repo}/releases/tags/{tag}"],
        text=True, capture_output=True,
    )
    if existing.returncode and "404" not in existing.stderr:
        raise RuntimeError(existing.stderr)
    should_build = bool(existing.returncode) or json.loads(existing.stdout).get("draft", False)
    with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
        for key, value in {
            "version": version, "sha": source, "tag": tag,
            "build": str(should_build).lower(), "upstream": upstream,
        }.items():
            stream.write(f"{key}={value}\n")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as stream:
        stream.write(f"Upstream: [{version}](https://github.com/rustdesk/rustdesk/releases/tag/{version})\n\n")
        stream.write(f"Custom source: `{source}`\n\nRelease: `{tag}`\n\nBuild required: `{should_build}`\n")


if __name__ == "__main__":
    main()

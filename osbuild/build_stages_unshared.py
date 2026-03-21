#!/usr/bin/python3

import contextlib
import json
import os
import subprocess
import sys
import tempfile

from osbuild.monitor import LogMonitor
from osbuild.objectstore import ObjectStore, ObjectFormat
from osbuild.pipeline import Stage, Runner


def untar(file, destination):
    subprocess.run([
        "tar", "--extract",
        "--file", file,
        "--directory", destination
    ], check=True)


def build_tree(workdir, build):
    directory = tempfile.TemporaryDirectory(dir=workdir, prefix="build-")
    if build:
        untar(build, directory.name)
    else:
        usr = os.path.join(directory.name, "usr")
        os.symlink("/usr", usr)

    return directory


def build_stages(tree, metadir, stages, base, store, build, runner, libdir):
    if base:
        untar(base, tree)

    results = []
    monitor = LogMonitor(sys.stdout.fileno())
    for stage in stages:
        monitor.stage(stage)

        with open(os.path.join(metadir, f"{stage.id}.json"), "w") as meta:
            r = stage.run(tree, meta.name, runner, build, store, monitor, libdir)

        results.append(r)

        with open(os.path.join(metadir, f"{stage.id}.json"), "r") as meta:
            monitor.result(r, json.load(meta))

        if not r.success:
            break

    return results


def main(args):
    libdir = args["libdir"]
    runner = Runner.from_dict(args["runner"], libdir)
    stages = [Stage.from_dict(s, libdir) for s in args["stages"]]
    base = args.get("base")
    workdir = args["workdir"]

    tree = os.path.join(workdir, "tree")
    os.makedirs(tree)
    metadir = os.path.join(workdir, "meta")
    os.makedirs(metadir)

    with ObjectStore(args["storedir"]) as store, build_tree(workdir, args.get("build")) as build:
        results = build_stages(tree, metadir, stages, base, store, build, runner, libdir)

    subprocess.run([
        "tar", "--create",
        "--file", os.path.join(workdir, "tree.tar"),
        "--remove-files",
        "--directory", tree,
        "."
    ], check=True)

    with open(os.path.join(workdir, "results.json"), "w") as f:
        json.dump([r.as_dict() for r in results], f)


if __name__ == '__main__':
    main(json.load(sys.stdin))

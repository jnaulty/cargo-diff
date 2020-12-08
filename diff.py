#!/bin/python3

'''
diff.py --crate tokio --initial_version 0.2.22 --final_version 0.3.4
'''

import argparse
import os
import tempfile
import subprocess
import requests

api = "https://crates.io"


def diff_crates(crate_name, version1, version2):
    # query crates.io
    url = api + "/api/v1/crates/" + crate_name
    r = requests.get(url)
    if r.status_code != 200:
        print("couldn't query crates.io")
        return
    result = r.json()

    # obtain url for the two versions
    versions = {}
    for version in result["versions"]:
        if version["num"] == version1:
            versions["version1"] = version["dl_path"]
        elif version["num"] == version2:
            versions["version2"] = version["dl_path"]

    if len(versions) != 2:
        print("couldn't find versions requested")
        print(result["versions"])
        return

    # obtain code for the two versions

    temp_dir = tempfile.TemporaryDirectory()
    subprocess.run(["wget", api + versions["version1"], "-O", "crate1.tar.gz"],
                   cwd=temp_dir.name)
    subprocess.run(["wget", api + versions["version2"], "-O", "crate2.tar.gz"],
                   cwd=temp_dir.name)
    subprocess.run(["mkdir", "out1"], cwd=temp_dir.name)
    subprocess.run(["mkdir", "out2"], cwd=temp_dir.name)
    subprocess.run(["tar", "-xvf", "crate1.tar.gz",
                    "-C", "out1"], cwd=temp_dir.name)
    path1 = subprocess.check_output(
        ["ls -d $PWD/*"], cwd=temp_dir.name + "/out1", shell=True).strip()
    subprocess.run(["tar", "-xvf", "crate2.tar.gz",
                    "-C", "out2"], cwd=temp_dir.name)
    path2 = subprocess.check_output(
        ["ls -d $PWD/*"], cwd=temp_dir.name + "/out2", shell=True).strip()
    print(path1)
    print(path2)

    # git diff -> html
    # npm install -g diff2html-cli
    report_file_name = f'{crate_name}.{version1}-{version2}.html'
    ps = subprocess.Popen(["git", "diff", "-u", path1, path2],
                          stdout=subprocess.PIPE)
    subprocess.run(["diff2html", "-s",
                    "line", "-F", report_file_name, "-d", "word", "-i", "stdin", "-o", "preview"], stdin=ps.stdout)

def parse_args():
    parser = argparse.ArgumentParser(description='Diff to versions of a cargo crate')
    parser.add_argument('--crate', type=str, dest='crate', required=True,
                                help='Name of Cargo Crate (e.g., tokio)')
    parser.add_argument('--initial_version', dest='initial_version', required=True,
                                help='initial version of cargo crate (e.g., 1.0.1)')
    parser.add_argument('--final_version', dest='final_version', required=True,
                                help='final version of cargo crate (e.g., 1.0.2)')

    args = parser.parse_args()
    return args

def main():

    args = parse_args()
    #diff_crates("tokio", "0.2.22", "0.3.4")
    diff_crates(args.crate, args.initial_version, args.final_version)


if __name__ == "__main__":
    main()

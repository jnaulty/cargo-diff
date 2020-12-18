#!/bin/python3

'''
diff.py --crate tokio --initial_version 0.2.22 --final_version 0.3.4
diff.py --crate <crate-name> --diff-repo --version <git-release-tag>
'''

import argparse
import os
import tempfile
import subprocess
import requests
import json

api = "https://crates.io"


def parse_guppy_diff(guppy_output_file: str, json_output: str):
    # figure out list of deps that have changed
    deps = []
    guppy_output = open(guppy_output_file, "r")
    guppy_output = json.loads(guppy_output.read())
    if "target-packages" in guppy_output and "changed" in guppy_output["target-packages"]:
        deps += guppy_output["target-packages"]["changed"]
    if "host-packages" in guppy_output and "changed" in guppy_output["host-packages"]:
        deps += guppy_output["host-packages"]["changed"]

    # for each changes, obtain name and version change
    output_files = []
    for dep in deps:
        name = dep["name"]

        # only care about updated dependencies
        if dep["change"] != "modified":
            continue
        # avoid internal dependencies
        if "workspace-path" in dep:
            continue
        # avoid non-version update changes
        if dep["old-version"] is None:
            continue
        # avoid non-crates.io deps
        if "crates-io" not in dep or dep["crates-io"] != True:
            print(f"{name} is not hosted on crates.io, skipping")
            continue

        old_version = dep["old-version"]
        new_version = dep["version"]
        if new_version != old_version:
            print(f"creating diff for {name} v{old_version} -> v{new_version}")
            # produce the diff files
            report = diff_crates(name, [old_version, new_version])
            output_files.append(report)

    # write json output to file?
    if json_output != "":
        f = open(json_output, "w")
        f.write(json.dumps(output_files))


def query_crates(crate_name: str):
    # query crates.io
    url = api + "/api/v1/crates/" + crate_name
    r = requests.get(url)
    if r.status_code != 200:
        print("couldn't query crates.io")
        return
    result = r.json()
    return result


def get_download_paths(result, versions):
    versions_dict = {}
    # get download path of crates tar archive
    for published_crate_version in result["versions"]:
        if published_crate_version["num"] in versions:
            versions_dict[published_crate_version["num"]] = {
                "dl_path": published_crate_version["dl_path"]
            }

    return versions_dict


def diff_crates(crate_name: str, versions: list):

    result = query_crates(crate_name)

    # obtain repository url from crates api

    git_repo = result["crate"]["repository"]

    versions_dict = get_download_paths(result, versions)
    # check to make sure found a dl_path for each version
    if len(versions_dict) != len(versions):
        print("ERROR: couldn't find versions requested")
        print(versions)
        print(versions_dict)
        print(result["versions"])
        return

    # extract code from the downloaded crate tar-archives
    temp_dir = tempfile.TemporaryDirectory()
    print(f"temp_dir = {temp_dir}")
    for version in versions:
        versioned_tar_archive_name = f"{crate_name}.{version}.tar.gz"
        versioned_output_dir = f"output_dir_{version}"

        subprocess.run(["wget", api + versions_dict[version]["dl_path"], "-O", versioned_tar_archive_name],
                       cwd=temp_dir.name)

        # create output directories
        subprocess.run(["mkdir", versioned_output_dir], cwd=temp_dir.name)

        subprocess.run(["tar", "-xvf", versioned_tar_archive_name,
                        "-C", versioned_output_dir], cwd=temp_dir.name)

        # get path of extracted tar-archive
        versioned_extracted_path = subprocess.check_output(
            ["ls -d $PWD/*"], cwd=f"{temp_dir.name}/{versioned_output_dir}", shell=True).strip()
        versions_dict[version]["extracted_path"] = versioned_extracted_path

    # compare two versions of the same crate from crates.io tar archive
    if len(versions) == 2:
        # get paths
        path1 = versions_dict[versions[0]]["extracted_path"]
        path2 = versions_dict[versions[1]]["extracted_path"]

        # debug
        print(path1)
        print(path2)

        # git diff -> html
        # npm install -g diff2html-cli

        # create 'standard' file-name
        report_file_name = f'{crate_name}.{versions[0]}-{versions[1]}.crates-diff.html'

        # diff the two different paths
        ps = subprocess.Popen(["git", "diff", "-u", path1, path2],
                              stdout=subprocess.PIPE)

        with open(f'{crate_name}.{versions[0]}-{versions[1]}.crates.diff', "w") as outfile:
            subprocess.run(["diff", "-r", path1, path2.decode('utf-8')],
                           stdout=outfile)
        # create html of the diff
        subprocess.run(["diff2html", "-s",
                        "line", "-F", report_file_name, "-d", "word", "-i", "stdin", "-o", "preview"], stdin=ps.stdout)
        return report_file_name

    # just compare a single version diff between git repo and crates.io tar archive
    elif len(versions) == 1:
        # download git repo, checkout git version, diff with version path
        git_tmp_dir = tempfile.TemporaryDirectory()
        subprocess.run(["mkdir", f"{git_tmp_dir.name}/{crate_name}"])

        # if tags were normalized...the following woud work
        #subprocess.run(["git", "clone", "--depth", "1", "--single-branch", "--branch", f"{versions[0]}", git_repo, f"{git_tmp_dir.name}/{crate_name}"])

        subprocess.run(["git", "clone", git_repo,
                        f"{git_tmp_dir.name}/{crate_name}"])
        tag_name_result = subprocess.run(
            ["git", "tag", "--list", f"*{versions[0]}*"], cwd=f"{git_tmp_dir.name}/{crate_name}", stdout=subprocess.PIPE)
        tag_name = tag_name_result.stdout.strip()
        print(f"checking out {tag_name}")
        subprocess.run(["git", "checkout", tag_name],
                       cwd=f"{git_tmp_dir.name}/{crate_name}")

        path1 = f"{git_tmp_dir.name}/{crate_name}"
        path2 = versions_dict[versions[0]]["extracted_path"]

        print("Path's created")
        print(path1)
        print(path2)

        # diff the two different paths
        ps = subprocess.Popen(["git", "diff", "-u", path1, path2],
                              stdout=subprocess.PIPE)
        with open(f'{crate_name}.{versions[0]}-crate-git.diff', "w") as outfile:
            subprocess.run(["diff", "-r", path1, path2.decode('utf-8')],
                           stdout=outfile)

        print(ps.stdout)
        # create 'standard' file-name
        report_file_name = f'{crate_name}.{versions[0]}-crate-git-diff.html'
        # create html of the diff
        print("creating diff2html report")
        subprocess.run(["diff2html", "-s",
                        "line", "-F", report_file_name, "-d", "word", "-i", "stdin", "-o", "preview"], stdin=ps.stdout)
        return report_file_name


def parse_args():
    parser = argparse.ArgumentParser(
        description='Diff to versions of a cargo crate')

    group = parser.add_mutually_exclusive_group()

    # analyze guppy-summaries output (multiple crates)
    group.add_argument('--guppy', type=str, dest='guppy', required=False,
                       help='guppy-summaries json output')
    parser.add_argument('--json-output', type=str, dest='json_output',
                        required=False, default="", help='guppy-summaries json output')

    # analyze a specific crate
    group.add_argument('--crate', type=str, dest='crate', required=False,
                       help='Name of Cargo Crate (e.g., tokio)')
    parser.add_argument('--initial_version', dest='initial_version', required=False,
                        help='initial version of cargo crate (e.g., 1.0.1)')
    parser.add_argument('--final_version', dest='final_version', required=False,
                        help='final version of cargo crate (e.g., 1.0.2)')
    parser.add_argument('--version', dest='version', required=False,
                        help='version of cargo crate (e.g., 1.0.2)')

    args = parser.parse_args()

    if args.version and (args.initial_version or args.final_version):
        parser.error(
            "can't use --version and --initial/final_version together")

    if bool(args.initial_version) != bool(args.final_version):
        parser.error(
            "--initial_version and --final_version must be used together")

    return args


def main():

    args = parse_args()
    #diff_crates("tokio", "0.2.22", "0.3.4")
    if args.guppy:
        parse_guppy_diff(args.guppy, args.json_output)
    if args.crate:
        if args.final_version:
            res = diff_crates(
                args.crate, [args.initial_version, args.final_version])
        elif args.version:
            diff_crates(args.crate, [args.version])


if __name__ == "__main__":
    main()

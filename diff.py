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

api = "https://crates.io"



def query_crates(crate_name: str):
    # query crates.io
    url = api + "/api/v1/crates/" + crate_name
    r = requests.get(url)
    if r.status_code != 200:
        print("couldn't query crates.io")
        return
    result = r.json()
    return result

def get_download_paths(result, versions, versions_dict: dict = {}):
    # get download path of crates tar archive
    for published_crate_version in result["versions"]:
        for requested_version in versions:
            if published_crate_version["num"] == requested_version:
                versions_dict[requested_version] = {"dl_path": published_crate_version["dl_path"]}

    # check to make sure found a dl_path for each version
    if len(versions_dict) != len(versions):
        print("ERROR: couldn't find versions requested")
        print(result["versions"])
        return

    return versions_dict

def diff_crates(crate_name: str, versions: list):
    
    result = query_crates(crate_name)


    # obtain repository url from crates api

    git_repo = result["crate"]["repository"]

    versions_dict = get_download_paths(result, versions)
    
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
        report_file_name = f'{crate_name}.{versions[0]}-{versions[1]}.html'

        # diff the two different paths
        ps = subprocess.Popen(["git", "diff", "-u", path1, path2],
                            stdout=subprocess.PIPE)
        
        with open(f'{crate_name}.{versions[0]}-{versions[1]}.crate.diff', "w") as outfile:
            subprocess.run(["diff", "-r", path1, path2.decode('utf-8')],
                        stdout=outfile)
        # create html of the diff
        subprocess.run(["diff2html", "-s",
                        "line", "-F", report_file_name, "-d", "word", "-i", "stdin", "-o", "preview"], stdin=ps.stdout)

    if len(versions) == 1:
        # download git repo, checkout git version, diff with version path
        git_tmp_dir = tempfile.TemporaryDirectory()
        subprocess.run(["mkdir", f"{git_tmp_dir.name}/{crate_name}"])

        # if tags were normalized...the following woud work
        #subprocess.run(["git", "clone", "--depth", "1", "--single-branch", "--branch", f"{versions[0]}", git_repo, f"{git_tmp_dir.name}/{crate_name}"])

        subprocess.run(["git", "clone", git_repo, f"{git_tmp_dir.name}/{crate_name}"])
        tag_name_result = subprocess.run(["git", "tag", "--list", f"*{versions[0]}*"], cwd=f"{git_tmp_dir.name}/{crate_name}", stdout=subprocess.PIPE)
        tag_name = tag_name_result.stdout.strip()
        print(f"checking out {tag_name}")
        subprocess.run(["git", "checkout", tag_name], cwd=f"{git_tmp_dir.name}/{crate_name}")

        path1 = f"{git_tmp_dir.name}/{crate_name}"
        path2 = versions_dict[versions[0]]["extracted_path"]

        print("Path's created")
        print(path1)
        print(path2)

        # diff the two different paths
        ps = subprocess.Popen(["git", "diff", "-u", path1, path2],
                            stdout=subprocess.PIPE)
        with open(f'{crate_name}.{versions[0]}-crate-git-diff', "w") as outfile:
            subprocess.run(["diff", "-r", path1, path2.decode('utf-8')],
                        stdout=outfile)

       

        print(ps.stdout)
        # create 'standard' file-name
        report_file_name = f'{crate_name}.{versions[0]}-crate-git-diff.html'
        # create html of the diff
        print("creating diff2html report")
        subprocess.run(["diff2html", "-s",
                        "line", "-F", report_file_name, "-d", "word", "-i", "stdin", "-o", "preview"], stdin=ps.stdout)



def parse_args():
    parser = argparse.ArgumentParser(description='Diff to versions of a cargo crate')
    parser.add_argument('--crate', type=str, dest='crate', required=True,
                                help='Name of Cargo Crate (e.g., tokio)')
    parser.add_argument('--initial_version', dest='initial_version', required=False,
                                help='initial version of cargo crate (e.g., 1.0.1)')
    parser.add_argument('--final_version', dest='final_version', required=False,
                                help='final version of cargo crate (e.g., 1.0.2)')
    parser.add_argument('--version', dest='version', required=False,
                                help='version of cargo crate (e.g., 1.0.2)')

    args = parser.parse_args()
    return args

def main():

    args = parse_args()
    #diff_crates("tokio", "0.2.22", "0.3.4")
    if args.final_version:
        diff_crates(args.crate, [args.initial_version, args.final_version])
    if args.version:
        diff_crates(args.crate, [args.version])


if __name__ == "__main__":
    main()

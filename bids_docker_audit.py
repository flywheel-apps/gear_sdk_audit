#!/bin/env python3

import json
import os

from exchange_audit_gears import full_pip_freeze, get_pip_list
from .commands.manage_sys import clean_up_docker
from .commands.scrape_dockerhub import get_list_of_repos, pull_repo

pwd = os.getcwd()
work_dir = os.path.join(pwd, "workdir")


def generate_list_from_docker(username, master_dict):
    """
    Generate a list of sites (flywheel, scitran, stanford, etc) based on folders in the
    exchange, and populate them with the manifests in that folder.  Then go into each
    folder/manifest, extract the docker image, and if it can be loaded, enter it and
    exctract the python and pip versions.  Then version match the pips to the pythons,
    and perform a pip freeze, storing the results. PHEW.

    """
    repos = get_list_of_repos(username)
    for repo in repos:
        repo_dict = {}
        if repo["name"] in master_dict:
            print("Already collected for {}".format(repo["name"]))
            continue
        # Initialize
        data_dict = {"repo", {repo["name"]}}
        tmp_dir = pull_repo(repo)
        py2pip, py_list, pip_list = get_pip_list(repo["name"])
        # py2pip = (py_path, py_vers, main_vers, pip_path, pip_vers)
        # py_list: (p, full_python_vers, mainv)
        # pip_list: (pip, pip_vers)

        full_py_list = []
        full_pip_list = []
        data_dict["Pythons"] = {}
        for pypath, pyvers, mainpy, pippath, pipvers in py2pip:

            if pypath not in full_py_list:
                full_py_list.append(pypath)
            if pippath not in full_pip_list:
                full_pip_list.append(pippath)

            if pippath == "":
                package_vers_dict = "Error Extracting Pip Version"
            else:
                pip_vers, package_vers_dict = full_pip_freeze(repo["name"], pippath)

            print("\n{} \t {}".format(repo["name"], pip_vers))

            # data_dict['Pythons'] = {}
            py_name = "python_{}".format(pyvers)
            if not py_name in data_dict["Pythons"]:
                data_dict["Pythons"][py_name] = {}
            data_dict["Pythons"][py_name]["python_dir"] = pypath
            data_dict["Pythons"][py_name]["python_version"] = pyvers

            if not "pips" in data_dict["Pythons"][py_name]:
                data_dict["Pythons"][py_name]["pips"] = {}

            pip_name = "pip_{}".format(pipvers)
            i = "a"
            while pip_name in data_dict["Pythons"][py_name]["pips"]:
                pip_name = "{}_{}".format(pip_name, i)
                i = chr(ord(i[0]) + 1)

            data_dict["Pythons"][py_name]["pips"][pip_name] = {}
            data_dict["Pythons"][py_name]["pips"][pip_name][
                "freeze"
            ] = package_vers_dict
            data_dict["Pythons"][py_name]["pips"][pip_name]["pip_dir"] = pippath
            data_dict["Pythons"][py_name]["pips"][pip_name]["pip_version"] = pipvers

        data_dict["Python_Dirs"] = full_py_list
        data_dict["Pip_Dirs"] = full_pip_list

        clean_up_docker(tmp_dir)
        repo_dict[repo["name"]] = data_dict

        master_dict[username] = repo_dict
        # Save after every site
        with open(os.path.join(work_dir, "master_json.json"), "w") as fp:
            json.dump(master_dict, fp)

    return master_dict


def docker_main(username="bids"):

    refresh = False

    json_out = os.path.join(work_dir, f"docker_{username}_master_json.json")
    if os.path.exists(json_out):
        print("Found previous run, loading...")
        with open(json_out, "r") as j:
            master_dict = json.load(j)
        print("...Done")
    else:
        master_dict = {}

    # Generate a list from the exchange files
    data = generate_list_from_docker(username, master_dict)

    # Save after every site
    with open(json_out, "w") as fp:
        json.dump(data, fp)


if __name__ == "__main__":
    docker_main()

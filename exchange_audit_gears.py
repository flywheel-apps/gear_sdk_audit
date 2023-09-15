#!/bin/env python3

import json
import os
import pathlib
import pprint
import re
import subprocess as sp

exchange_repo = "https://github.com/flywheel-io/exchange.git"
pwd = os.getcwd()
work_dir = os.path.join(pwd, "workdir")


def download_repo(refresh):
    exchange_dir = os.path.join(work_dir, "flywheel")
    if not refresh and not os.path.exists(exchange_dir):
        cmd = ["git", "clone", exchange_repo, exchange_dir]
        try:
            sp.run(cmd)
        except:
            raise Exception("Couldnt git pull the repo {}".format(exchange_repo))

    return exchange_dir


def match_pip_to_py(pip_versions, docker_image):
    """
    This looks for all python versions in a docker image PATH variable, and matches them
    by version to pip's found in the docker image's PATH variable (by version).  If a
    python does not have a matching pip, then the python is skipped and no information
    is stored on it.  Only pythons with pips are used so that "pip freeze" can be
    called.  If there are multiple pips that match a python, all possible matches are
    listed.

    """

    # First get path pythons:
    cmd = [
        "sudo",
        "docker",
        "run",
        "--env",
        "LD_LIBRARY_PATH=''",
        "--rm",
        "-ti",
        "--entrypoint=/bin/bash",
        "-v",
        "{}/commands:/tmp/my_commands".format(pwd),
        docker_image,
        "/tmp/my_commands/bash_crawl.sh",
        "python*",
    ]

    print(" ".join(cmd))
    r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    r.wait()
    output = str(r.stdout.read())
    print(output)
    output = output.split("\n")

    exp = ".*python([0-9]?\.?[0-9]?[0-9]?\.?[0-9]?[0-9]?)$"
    py_list = []

    for result in output:
        m = None
        m = re.match(exp, result)
        if not m == None:
            p = pathlib.Path(result.rstrip())
            print("{} poiting to {}".format(p, p.resolve()))
            p = p.resolve().as_posix()

            cmd = [
                "sudo",
                "docker",
                "run",
                "--env",
                "LD_LIBRARY_PATH=''",
                "--rm",
                "-ti",
                "--entrypoint={}".format(p),
                docker_image,
                "--version",
            ]

            print(" ".join(cmd))
            r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
            r.wait()
            output = str(r.stdout.read().rstrip())
            print('python version: "{}"'.format(output))
            # output = str(r.stdout.read().rstrip())
            if output == "":
                continue

            full_python_vers = output.split()[-1]
            vlist = full_python_vers.split(".")
            if len(vlist) > 2:
                mainv = ".".join(vlist[0:2])
            else:
                mainv = full_python_vers

            pair = (p, full_python_vers, mainv)
            if pair not in py_list:
                print("adding {}".format(p))
                py_list.append(pair)

    pprint.pprint(py_list)
    pprint.pprint(pip_versions)
    py_2_pip = []

    for pip_path, pip_vers in pip_versions:
        # python_match = []

        # pip_dir = os.path.dirname(pip_path)
        # ANY python that matches the pip version gets added
        # No pip for your python version?  No dice.
        for py_path, py_vers, main_vers in py_list:
            if main_vers == pip_vers:
                new_py2pip = (py_path, py_vers, main_vers, pip_path, pip_vers)
                if new_py2pip not in py_2_pip:
                    py_2_pip.append(new_py2pip)

    pprint.pprint(py_2_pip)

    return (py_2_pip, py_list)


def get_pip_list(docker_image):
    """
    This function looks for pips in a python environment.  If none are found, a generic
    "pip","pip2", and "pip3" are tried, mostly for shits and giggles, but it never works
    I don't think.
    """
    # First try bash crawl (won't work with alpine)
    cmd = [
        "sudo",
        "docker",
        "run",
        "--env",
        "LD_LIBRARY_PATH=''",
        "--rm",
        "-ti",
        "--entrypoint=/bin/bash",
        "-v",
        "{}/commands:/tmp/my_commands".format(pwd),
        docker_image,
        "/tmp/my_commands/bash_crawl.sh",
        "pip*",
    ]

    print(" ".join(cmd))
    r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    r.wait()
    output = str(r.stdout.read())
    print("output:")
    print(output)

    output = output.split("\n")

    exp = ".*pip([0-9]?\.?[0-9]?[0-9]?\.?[0-9]?[0-9]?)$"
    pip_list = []
    for result in output:
        m = None
        m = re.match(exp, result)
        if not m == None:
            new_pip = result.rstrip()
            if not new_pip in pip_list:
                pip_list.append(new_pip)

    if pip_list == []:
        pip_list = ["pip", "pip2", "pip3"]

    pip_dir_list = []
    pip_ver_list = []

    pip_vers_list = []
    for pip in pip_list:
        cmd = [
            "sudo",
            "docker",
            "run",
            "--env",
            "LD_LIBRARY_PATH=''",
            "--rm",
            "-ti",
            "--entrypoint={}".format(pip),
            docker_image,
            "--version",
        ]

        print(" ".join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
        output = str(r.stdout.read())
        try:
            pip_vers = output.split()[-1][:-1]
            pip_dir = os.path.dirname(pip)
            if pip_dir in pip_dir_list and pip_vers in pip_ver_list:
                continue
            pip_vers_list.append((pip, pip_vers))

            pip_dir_list.append(pip_dir)
            pip_ver_list.append(pip_vers)

        except Exception as e:
            print("no pip version in {}".format(output))
            print(e)

    # pprint.pprint(pip_vers_list)

    py2pip, py_list = match_pip_to_py(pip_vers_list, docker_image)

    return (py2pip, py_list, pip_vers_list)


def full_pip_freeze(docker_image, pip):
    """
    for a given pip/docker image combo, performs a full pip freeze and stores the result
    """

    match = None
    pip_vers = None

    try:

        cmd = [
            "sudo",
            "docker",
            "run",
            "--env",
            "LD_LIBRARY_PATH=''",
            "--rm",
            "-ti",
            "--entrypoint={}".format(pip),
            docker_image,
            "freeze",
        ]

        print(" ".join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
        raw_output = str(r.stdout.read())

        package_vers_dict = {}
        raw_output = raw_output.split("\n")
        output = []

        for op in raw_output:
            if op.find("==") > -1:
                output.append(op)

        if len(output) == 0:
            print("No packages for pip {}".format(pip_vers))
            return (pip_vers, {})

        output = [item.split("==") for item in output]

        for val in output:
            package_vers_dict[val[0]] = val[1]

    except Exception as e:
        print("error extractiong pip info")
        print(e)

    return (pip_vers, package_vers_dict)


def find_gear_in_other_site(gear_name, gear_vers, master_dict):
    """
    Checks to see if this gear (at this version) already exists and was recorded from
    another site/instance.  If it is already in the master dict, we just use that value.

    """
    found = False
    prev_dict = {}
    for prev_site, site_gears in master_dict.items():
        if gear_name in site_gears.keys():
            if "gear-version" in site_gears[gear_name].keys():
                if site_gears[gear_name]["gear-version"] == gear_vers:
                    print(
                        "Found gear {} v{} in {}".format(
                            gear_name, gear_vers, prev_site
                        )
                    )
                    prev_dict = site_gears[gear_name]
                    found = True
                    return (found, prev_dict)
    return (found, prev_dict)


def get_install_date(gear_name, gear_dict):
    """
    Currently not used anywhere.  But self explanatory. 

    """
    date = "unknown"
    if gear_name in gear_dict.keys():
        date = gear_dict[gear_name].created
        date = "{day}/{month}/{year}".format(
            day=date.day, month=date.month, year=date.year
        )

    return date


def generate_list_from_exchange(manifest_dir, master_dict):
    """
    Generate a list of sites (flywheel, scitran, stanford, etc) based on folders in the
    exchange, and populate them with the manifests in that folder.  Then go into each
    folder/manifest, extract the docker image, and if it can be loaded, enter it and
    exctract the python and pip versions.  Then version match the pips to the pythons,
    and perform a pip freeze, storing the results. PHEW.

    """
    print(manifest_dir)

    print("Gear Name \t image \t\t sdk-version")

    ############ Loop through manifests in the exchange:
    for root, dirs, files in os.walk(manifest_dir):
        site_dict = {}
        print("\n" + root + "\n")

        site = os.path.split(root)[-1]
        if site in master_dict:
            print("Already collected for {}".format(site))
            continue

        for file in files:

            api_enabled = False
            # Initialize my Data Dict
            data_dict = {
                "gear-name": "",
                "gear-label": "",
                "custom-docker-image": "",
                "gear-version": "",
                "site": "",
                "api-enabled": "",
            }

            file = os.path.join(root, file)
            try:
                base, ext = os.path.splitext(file)

                if ext == ".json":
                    mn = open(file).read()
                    # print(file)
                    if mn.find("api-key") != -1:
                        api_enabled = True

                    mn = json.load(open(file))
                    gear_name = mn["name"]
                    gear_label = mn["label"]
                    gear_version = mn["version"]

                    found, previous_dict = find_gear_in_other_site(
                        gear_name, gear_version, master_dict
                    )
                    if found:
                        site_dict[gear_name] = previous_dict
                        continue

                    try:
                        docker_image = mn["custom"]["docker-image"]
                    except:
                        try:
                            docker_image = mn["custom"]["gear-builder"]["image"]
                        except:
                            docker_image = "unknown"

                    # gear_date = get_install_date(gear_name, gear_dict)

                    py2pip, py_list, pip_list = get_pip_list(docker_image)
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
                            pip_vers, package_vers_dict = full_pip_freeze(
                                docker_image, pippath
                            )

                        print(
                            "\n{} \t {} \t {}".format(gear_name, docker_image, pip_vers)
                        )

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
                        data_dict["Pythons"][py_name]["pips"][pip_name][
                            "pip_dir"
                        ] = pippath
                        data_dict["Pythons"][py_name]["pips"][pip_name][
                            "pip_version"
                        ] = pipvers

                    data_dict["Python_Dirs"] = full_py_list
                    data_dict["Pip_Dirs"] = full_pip_list
                    data_dict["gear-name"] = gear_name
                    data_dict["gear-label"] = gear_label
                    data_dict["gear-version"] = gear_version
                    data_dict["custom-docker-image"] = docker_image
                    data_dict["site"] = site
                    data_dict["api-enabled"] = api_enabled

                    cmd = ["sudo", "docker", "image", "rm", docker_image]
                    print(" ".join(cmd))
                    r = sp.Popen(
                        cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True
                    )
                    r.wait()
                    site_dict[gear_name] = data_dict

            except Exception as e:
                print("Unable to extract info from {}".format(os.path.join(root, file)))
                # raise(e)
                print(e)

        master_dict[site] = site_dict
        # Save after every site
        with open(os.path.join(work_dir, "master_json.json"), "w") as fp:
            json.dump(master_dict, fp)

    return master_dict


def exchange_main():

    refresh = False

    json_out = os.path.join(work_dir, "exchange_master_json.json")
    if os.path.exists(json_out):
        print("Found previous run, loading...")
        with open(json_out, "r") as j:
            master_dict = json.load(j)
        print("...Done")
    else:
        master_dict = {}

    exchange_dir = download_repo(refresh)
    manifest_dir = os.path.join(exchange_dir, "gears")

    if not os.path.exists(manifest_dir):
        raise Exception("No manifest directory found in repo")

    # Generate a list from the exchange files
    data = generate_list_from_exchange(manifest_dir, master_dict)

    # Save after every site
    with open(json_out, "w") as fp:
        json.dump(data, fp)


if __name__ == "__main__":
    exchange_main()

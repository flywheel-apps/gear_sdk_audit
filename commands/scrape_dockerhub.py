import subprocess as sp

import requests
from bs4 import BeautifulSoup
from manage_sys import create_temp_dir

url = "https://hub.docker.com/u/bids"


def get_list_of_repos(username="bids"):
    # Send a GET request to the Docker Hub API to retrieve the list of repositories
    url = f"https://hub.docker.com/v2/repositories/{username}"
    response = requests.get(url)
    repositories = response.json()
    return repositories


def pull_repo(repo):
    """
    Returns:
        temp_dir (Path): Clean-up the temp_dir after the pip matching and processing
    """
    tmp_dir = create_temp_dir()
    repository_name = repo["name"]

    try:
        # Run the 'docker pull' command to pull the image into the temporary directory
        pull_command = f"docker pull {repository_name}"
        sp.call(pull_command, shell=True)
        print(
            f"Image '{repository_name}' pulled successfully into the temporary directory: {temp_dir}"
        )
        return tmp_dir
    except Exception as e:
        print(f"Error pulling image '{repository_name}': {str(e)}")

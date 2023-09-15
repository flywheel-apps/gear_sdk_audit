import subprocess as sp

import requests
from commands.manage_sys import create_temp_dir

url = "https://hub.docker.com/u/bids"

def docker_login():
    try:
        # Run the 'docker login' command with the provided username and token
        login_command = f"docker login"
        sp.run(login_command, check=True, text=True, shell=True)
        print("Successfully logged in to Docker Hub.")
    except sp.CalledProcessError as e:
        print(f"Error logging in to Docker Hub: {e.output}")
def get_list_of_repos(username="bids"):
    # Send a GET request to the Docker Hub API to retrieve the list of repositories
    url = f"https://hub.docker.com/v2/repositories/{username}"
    response = requests.get(url)
    repositories = response.json()
    return repositories


def pull_repo(repo, work_dir):
    """
    Returns:
        temp_dir (Path): Clean-up the temp_dir after the pip matching and processing
    """
    tmp_dir = create_temp_dir(work_dir)
    repository_name = repo['namespace']+'/'+repo["name"]

    try:
        # Run the 'docker pull' command to pull the image into the temporary directory
        pull_command = f"docker pull {repository_name}"
        sp.call(pull_command, shell=True)
        print(
            f"Image '{repository_name}' pulled successfully into the temporary directory: {tmp_dir}"
        )
        return tmp_dir, repository_name
    except Exception as e:
        print(f"Error pulling image '{repository_name}': {str(e)}")

import os
import shutil
import subprocess as sp
from pathlib import Path


def clean_up_docker(tmp_dir, docker_image):
    try:
        cmd = ["docker", "image", "rm", docker_image]
        print(" ".join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
    except Exception as e:
        print(e)
    finally:
        shutil.rmtree(tmp_dir)
        print(f"Temporary directory '{tmp_dir}' removed")


def create_temp_dir(work_dir):
    # Create a temporary directory
    tmp_dir = Path(work_dir)/'tmp_docker_img'
    tmp_dir.mkdir(parents=True, exist_ok=True)
    print(f"Temporary directory created: {tmp_dir}")

    # Change the current working directory to the temporary directory
    os.chdir(tmp_dir)
    print(f"Changed current working directory to: {tmp_dir}")

    return tmp_dir

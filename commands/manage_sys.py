import os
import shutil
import subprocess as sp
import tempfile


def clean_up_docker(tmp_dir, docker_image):
    try:
        cmd = ["sudo", "docker", "image", "rm", docker_image]
        print(" ".join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
    except Exception as e:
        print(e)
    finally:
        shutil.rmtree(tmp_dir)
        print(f"Temporary directory '{tmp_dir}' removed")


def create_temp_dir():
    # Create a temporary directory
    tmp_dir = tempfile.mkdtemp()
    print(f"Temporary directory created: {tmp_dir}")

    # Change the current working directory to the temporary directory
    os.chdir(tmp_dir)
    print(f"Changed current working directory to: {tmp_dir}")

    return tmp_dir

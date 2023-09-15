import subprocess as sp
def get_os_details(image_name):
    command = f"docker run --rm --entrypoint /bin/sh {image_name} -c \"cat /etc/os-release | grep PRETTY_NAME\""
    try:
        result = sp.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            print(output)
            return output
        else:
            error = result.stderr
            print(f"Command execution failed: {error}")
    except sp.CalledProcessError as e:
        print(f"Error executing command: {e}")
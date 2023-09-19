import subprocess as sp
import re
def get_os_details(image_name):
    command = f"docker run --rm --entrypoint /bin/sh {image_name} -c \"cat /etc/os-release | grep PRETTY_NAME\""
    try:
        result = sp.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            output = clean_pretty_name(result.stdout)
            print(output)
            return output
        else:
            error = result.stderr
            print(f"Command execution failed: {error}")
    except sp.CalledProcessError as e:
        print(f"Error executing command: {e}")

def clean_pretty_name(pretty_name):
    # Define the pattern to match the value within double quotes
    pattern = r'"([^"]*)"'

    # Find the first occurrence of the pattern in the string
    match = re.search(pattern, pretty_name)

    if match:
        result = match.group(1)  # Get the matched value within double quotes
        return result
import subprocess
from config import debug

def get_path_no_ext(path, extension_no=1):
    """Function for getting the path without extension.

    Args:
        path (str): Path to the file.
        extension_no (int, optional): Which extension should it stop on. E.g. for file sample.bam.bai, can return either "sample" (for extension_no=2) or "sample.bam" (for extension_no=1), depending on this parameter. Defaults to 1.

    Returns:
        str: Modified path.
    """
    return ".".join(path.split(".")[0:-extension_no])

def get_path(path, extension_no=1):
    """Returns directory the file is in.

    Args:
        path (str): Full path to the file.
        extension_no (int, optional): The directory to return - if 1, it returns file directory, if larget it returns the next scoped directory. Defaults to 1.

    Returns:
        str: Modified path.
    """
    return "/".join(path.split("/")[0:-extension_no])+"/"

def run_command(command, conda_env=None):
    """Function for running CLI commands.

    Args:
        command (str): Command to run.
        conda_env (str, optional): Name of the conda environment to use. If None, runs default one. Defaults to None.
    """
    if(conda_env):
        command = "bash -c \"source activate %s; %s\"" % (conda_env, command)
    if(debug >= 1):
        print("___COMMAND: " + command)
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if(debug >= 2):
        print("___OUTPUT:")
        print(process.stdout)
    print(process.stderr)
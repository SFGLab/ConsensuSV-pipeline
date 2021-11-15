import subprocess

def get_path_no_ext(path, extension_no=1):
    return ".".join(path.split(".")[0:-extension_no])

def get_path(path, extension_no=1):
    return "/".join(path.split("/")[0:-extension_no])+"/"

def run_command(command, conda_env=None):
    if(conda_env):
        command = "bash -c \"source activate %s; %s\"" % (conda_env, command)
    if(debug >= 1):
        print("___COMMAND: " + command)
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if(debug >= 2):
        print("___OUTPUT:")
        print(process.stdout)
    print(process.stderr)
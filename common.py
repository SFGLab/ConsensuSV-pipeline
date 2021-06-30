import subprocess

reference_genome = "/tools/GRCh38_full_analysis_set_plus_decoy_hla.fa"
debug = 1

def get_path_no_ext(path, extension_no=1):
    return ".".join(path.split(".")[0:-extension_no])

def run_command(command, condaEnv=None):
        if(condaEnv):
            command = "bash -c \"source activate %s; %s\"" % (condaEnv, command)
        if(debug):
            print("___COMMAND: " + command)
        result = subprocess.getoutput(command)
        if(debug):
            print("___OUTPUT:" + result)
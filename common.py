import subprocess

reference_genome = "/tools/GRCh38_full_analysis_set_plus_decoy_hla.fa"
debug = 1
all_chromosomes = "chr1,chr2,chr3,chr4,chr5,chr6,chr7,chr8,chr9,chr10,chr11,chr12,chr13,chr14,chr15,chr16,chr17,chr18,chr19,chr20,chr21,chr22,chrX,chrY,chrM"
def get_path_no_ext(path, extension_no=1):
    return ".".join(path.split(".")[0:-extension_no])

def run_command(command, conda_env=None, return_output=False):
        if(conda_env):
            command = "bash -c \"source activate %s; %s\"" % (conda_env, command)
        if(debug):
            print("___COMMAND: " + command)
        result = subprocess.getoutput(command)
        if(debug):
            print("___OUTPUT:" + result)
        if(return_output):
            return result
import subprocess

reference_genome = "/tools/GRCh38_full_analysis_set_plus_decoy_hla.fa"
debug = 1
all_chromosomes = "chr1,chr2,chr3,chr4,chr5,chr6,chr7,chr8,chr9,chr10,chr11,chr12,chr13,chr14,chr15,chr16,chr17,chr18,chr19,chr20,chr21,chr22,chrX,chrY,chrM"
threads_samtools = 4

def get_path_no_ext(path, extension_no=1):
    return ".".join(path.split(".")[0:-extension_no])

def get_path(path, extension_no=1):
    return "/".join(path.split("/")[0:-extension_no])+"/"

def run_command(command, conda_env=None):
        if(conda_env):
            command = "bash -c \"source activate %s; %s\"" % (conda_env, command)
        if(debug):
            print("___COMMAND: " + command)
        if(debug):
            print("___OUTPUT:")
        process = subprocess.run(command, capture_output=(not debug), shell=True)
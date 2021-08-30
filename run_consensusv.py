from sv_callings import CallVariants
from common import reference_genome, debug, run_command, get_path, all_chromosomes, get_path_no_ext, no_threads
import luigi
import os
import shutil

class Train1000G(luigi.Task):

    def requires(self):
        return [CallVariants(sample_name="HG00512", train_1000g=True),
        CallVariants(sample_name="HG00513", train_1000g=True),
        CallVariants(sample_name="HG00514", train_1000g=True),
        CallVariants(sample_name="HG00731", train_1000g=True),
        CallVariants(sample_name="HG00732", train_1000g=True),
        CallVariants(sample_name="HG00733", train_1000g=True),
        CallVariants(sample_name="NA19238", train_1000g=True),
        CallVariants(sample_name="NA19239", train_1000g=True),
        CallVariants(sample_name="NA19240", train_1000g=True)]

    def output(self):
        return luigi.LocalTarget("1000g_illumina.model")

    def run(self):
        run_command("python /tools/ConsensuSV-1.0/main.py -f /pipeline/ -t")

if __name__ == '__main__':
    luigi.run()
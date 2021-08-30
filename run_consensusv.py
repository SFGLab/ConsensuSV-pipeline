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
        shutil.copyfile("truth_samples/HG00512.vcf", "/pipeline/HG00512/truth.vcf")
        shutil.copyfile("truth_samples/HG00513.vcf", "/pipeline/HG00513/truth.vcf")
        shutil.copyfile("truth_samples/HG00514.vcf", "/pipeline/HG00514/truth.vcf")
        shutil.copyfile("truth_samples/HG00731.vcf", "/pipeline/HG00731/truth.vcf")
        shutil.copyfile("truth_samples/HG00732.vcf", "/pipeline/HG00732/truth.vcf")
        shutil.copyfile("truth_samples/HG00733.vcf", "/pipeline/HG00733/truth.vcf")
        run_command("python /tools/ConsensuSV-1.0/main.py -f /pipeline/ -t")

if __name__ == '__main__':
    luigi.run()
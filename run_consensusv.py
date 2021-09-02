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
        return luigi.LocalTarget("/tools/ConsensuSV-1.0/1000g_illumina.model")

    def run(self):
        shutil.copyfile("truth_samples/HG00512.vcf", "/pipeline/HG00512/truth.vcf")
        shutil.copyfile("truth_samples/HG00513.vcf", "/pipeline/HG00513/truth.vcf")
        shutil.copyfile("truth_samples/HG00514.vcf", "/pipeline/HG00514/truth.vcf")
        shutil.copyfile("truth_samples/HG00731.vcf", "/pipeline/HG00731/truth.vcf")
        shutil.copyfile("truth_samples/HG00732.vcf", "/pipeline/HG00732/truth.vcf")
        shutil.copyfile("truth_samples/HG00733.vcf", "/pipeline/HG00733/truth.vcf")
        run_command("python -u /tools/ConsensuSV-1.0/main.py -f /pipeline/ -t -s HG00512,HG00513,HG00514,HG00731,HG00732,HG00733 -c breakdancer,breakseq,cnvnator,delly,lumpy,manta,tardis,whamg -mod 1000g_illumina.model")

class Benchmark1000G(luigi.Task):

    def requires(self):
        return [Train1000G()]

    def output(self):
        return luigi.LocalTarget("benchmark.txt")

    def run(self):
        run_command("python -u /tools/ConsensuSV-1.0/main.py -f /pipeline/ -s HG00512,HG00513,HG00514,HG00731,HG00732,HG00733,NA19238,NA19239,NA19240 -mod 1000g_illumina.model")
        run_command("python -u /tools/ConsensuSV-1.0/charles_filter_n.py -s HG00512,HG00513,HG00514,HG00731,HG00732,HG00733,NA19238,NA19239,NA19240 -o /tools/ConsensuSV-1.0/output/consensuSV__HG00512.vcf,/tools/ConsensuSV-1.0/output/consensuSV__HG00513.vcf,/tools/ConsensuSV-1.0/output/consensuSV__HG00514.vcf,/tools/ConsensuSV-1.0/output/consensuSV__HG00731.vcf,/tools/ConsensuSV-1.0/output/consensuSV__HG00732.vcf,/tools/ConsensuSV-1.0/output/consensuSV__HG00733.vcf,/tools/ConsensuSV-1.0/output/consensuSV__NA19238.vcf,/tools/ConsensuSV-1.0/output/consensuSV__NA19239.vcf,/tools/ConsensuSV-1.0/output/consensuSV__NA19240.vcf > benchmark.txt")

class RunConsensuSV(luigi.Task):

    def requires(self):
        return [CallVariants(sample_name="HG00512", train_1000g=True)]

    def output(self):
        return luigi.LocalTarget("/tools/ConsensuSV-1.0/1000g_illumina.model")

    def run(self):
        run_command("python -u /tools/ConsensuSV-1.0/main.py -f /pipeline/ -s SRR590764 -mod 1000g_illumina.model")

if __name__ == '__main__':
    luigi.run()
from align_genome import PerformAlignment
from common import reference_genome, debug, run_command, get_path, all_chromosomes, get_path
import luigi
import os
import shutil

class Train1000G(luigi.Task):

    def requires(self):
        return [CallVariants(sample_name="HG00512")]

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+".bam.bai")

    def run(self):
        if(self.already_done):
            run_command("samtools index %s" % "/pipeline/"+self.sample_name+"/"+self.sample_name+".bam")
        else:
            run_command("samtools index %s" % self.input().path)
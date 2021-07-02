import luigi
import os

from common import reference_genome, debug, run_command, get_path_no_ext

class QCAnalysis(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def output(self):
        return [luigi.LocalTarget("/pipeline/"+get_path_no_ext(self.file_name_1).split("/")[-1]+'_fastqc.html'), 
        luigi.LocalTarget("/pipeline/"+get_path_no_ext(self.file_name_2).split("/")[-1]+'_fastqc.html')]

    def run(self):
        run_command("fastqc -f fastq -o %s %s" % ("/pipeline/", self.file_name_1))
        run_command("fastqc -f fastq -o %s %s" % ("/pipeline/", self.file_name_2))

class AlignGenome(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return QCAnalysis(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget("/pipeline/"+self.sample_name+'.sam')

    def run(self):
        command = "bwa mem -t 1 -B 4 -O 6 -E 1 -M -R \"@RG\\tID:SRR\\tLB:LIB_1\\tSM:SAMPLE_1\\tPL:ILLUMINA\" %s %s %s > %s" % \
        (reference_genome, self.file_name_1, self.file_name_2, "/pipeline/"+self.sample_name+'.sam')

        run_command(command)

class ConvertToBam(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return AlignGenome(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+".bam")

    def run(self):
        full_path_output = get_path_no_ext(self.input().path)+".bam"
        run_command("samtools view -S -b %s > %s" % (self.input().path, full_path_output))

class SortBam(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return ConvertToBam(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+"_sorted.bam")

    def run(self):
        full_path_output = get_path_no_ext(self.input().path)+"_sorted.bam"
        run_command("samtools sort %s > %s" % (self.input().path, full_path_output))

class IndexBam(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return SortBam(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(self.input().path+".bai")

    def run(self):
        run_command("samtools index %s" % self.input().path)

class BaseRecalibrator(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    known_sites = "/tools/ALL_20141222.dbSNP142_human_GRCh38.snps.vcf.gz"

    def requires(self):
        return IndexBam(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path, 2)+".recal_table")

    def run(self):
        input_file = get_path_no_ext(self.input().path, 2)+".bam"
        recal_table = get_path_no_ext(input_file)+".recal_table"

        run_command("gatk BaseRecalibrator -R %s -O %s -I %s -known-sites %s" % (reference_genome, recal_table, input_file, self.known_sites))

class ApplyBQSR(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return BaseRecalibrator(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+"_final.bam")

    def run(self):
        recal_table = self.input().path
        input_file = get_path_no_ext(recal_table)+".bam"
        output_file = get_path_no_ext(recal_table)+"_final.bam"

        run_command("gatk ApplyBQSR -R %s -O %s -I %s -bqsr-recal-file %s" % (reference_genome, output_file, input_file, recal_table))

class SortFinal(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return ApplyBQSR(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+"_sorted.bam")

    def run(self):
        input_file = get_path_no_ext(self.input().path)+"_sorted.bam"
        output_file = get_path_no_ext(self.input().path)+"_sorted.bam"

        run_command("samtools sort %s > %s" % (self.input().path, output_file))

class IndexFinal(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return SortFinal(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+".bam.bai")

    def run(self):
        run_command("samtools index %s" % self.input().path)

class PerformAlignment(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def output(self):
        return [luigi.LocalTarget("/pipeline/"+self.sample_name+"_preprocessed.bam"), luigi.LocalTarget("/pipeline/"+self.sample_name+"_preprocessed.bam.bai")]

    def run(self):
        os.remove("/pipeline/"+self.sample_name+".sam")
        os.remove("/pipeline/"+self.sample_name+".bam")
        os.remove("/pipeline/"+self.sample_name+"_sorted.bam")
        os.remove("/pipeline/"+self.sample_name+"_sorted.bam.bai")
        os.remove("/pipeline/"+self.sample_name+"_sorted.recal_table")
        os.remove("/pipeline/"+self.sample_name+"_sorted_final.bam")
        os.remove("/pipeline/"+self.sample_name+"_sorted_final.bai")
        os.rename("/pipeline/"+self.sample_name+"_sorted_final_sorted.bam", "/pipeline/"+self.sample_name+"_preprocessed.bam")
        os.rename("/pipeline/"+self.sample_name+"_sorted_final_sorted.bam.bai", "/pipeline/"+self.sample_name+"_preprocessed.bam.bai")

    def requires(self):
        return IndexFinal(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)



if __name__ == '__main__':
    luigi.run()

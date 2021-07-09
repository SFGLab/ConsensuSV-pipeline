import luigi
import os
import urllib.request 
import shutil
from common import reference_genome, debug, run_command, get_path_no_ext, threads_samtools
import socket

class QCAnalysis(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def output(self):
        return [luigi.LocalTarget("/pipeline/"+self.sample_name+"/"+get_path_no_ext(self.file_name_1).split("/")[-1]+'_fastqc.html'), 
        luigi.LocalTarget("/pipeline/"+self.sample_name+"/"+get_path_no_ext(self.file_name_2).split("/")[-1]+'_fastqc.html')]

    def run(self):
        dirpath = "/pipeline/%s/" % self.sample_name
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            shutil.rmtree(dirpath)
        os.makedirs(os.path.dirname(dirpath))
        run_command("fastqc -f fastq -o %s %s" % ("/pipeline/"+self.sample_name+"/", self.file_name_1))
        run_command("fastqc -f fastq -o %s %s" % ("/pipeline/"+self.sample_name+"/", self.file_name_2))

class AlignGenome(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return QCAnalysis(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget("/pipeline/"+self.sample_name+'/'+self.sample_name+'.sam')

    def run(self):
        command = "bwa mem -t 1 -B 4 -O 6 -E 1 -M -R \"@RG\\tID:SRR\\tLB:LIB_1\\tSM:SAMPLE_1\\tPL:ILLUMINA\" %s %s %s > %s" % \
        (reference_genome, self.file_name_1, self.file_name_2, "/pipeline/"+self.sample_name+'/'+self.sample_name+'.sam')

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
        run_command("samtools view -S -b -o %s -@ %s %s" % (full_path_output, threads_samtools, self.input().path,))

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
        run_command("samtools sort -o %s -@ %s %s" % (full_path_output, threads_samtools, self.input().path))

class IndexBam(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return SortBam(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(self.input().path+".bai")

    def run(self):
        run_command("samtools index -@ %s %s " % (threads_samtools, self.input().path))

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
    already_done = luigi.Parameter(default=False)
    train_1000g = luigi.Parameter(default=False)

    def requires(self):
        if(self.train_1000g):
            return Get1000G(sample_name=self.sample_name)
        elif(self.already_done):
            return None
        else:        
            return ApplyBQSR(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+"_sorted.bam")

    def run(self):
        input_file = get_path_no_ext(self.input().path)+"_sorted.bam"
        output_file = get_path_no_ext(self.input().path)+"_sorted.bam"

        run_command("samtools sort -o %s -@ %s %s" % (output_file, threads_samtools, self.input().path))

class IndexFinal(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()
    already_done = luigi.Parameter(default=False)
    train_1000g = luigi.Parameter(default=False)

    def requires(self):
        return SortFinal(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, already_done=self.already_done, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+".bam.bai")

    def run(self):
        if(self.already_done):
            run_command("samtools index -@ %s %s" % (threads_samtools, "/pipeline/"+self.sample_name+"/"+self.sample_name+".bam"))
        else:
            run_command("samtools index -@ %s %s" % (threads_samtools, self.input().path))

class Get1000G(luigi.Task):
    sample_name = luigi.Parameter()
    ftp_link = "ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/hgsv_sv_discovery/data"

    samples_ftp = {"HG00512": ftp_link+"/CHS/HG00512/high_cov_alignment/HG00512.alt_bwamem_GRCh38DH.20150715.CHS.high_coverage.cram",
    "HG00513": ftp_link+"/CHS/HG00513/high_cov_alignment/HG00513.alt_bwamem_GRCh38DH.20150715.CHS.high_coverage.cram",
    "HG00514": ftp_link+"/CHS/HG00514/high_cov_alignment/HG00514.alt_bwamem_GRCh38DH.20150715.CHS.high_coverage.cram",
    "HG00731": ftp_link+"/PUR/HG00731/high_cov_alignment/HG00731.alt_bwamem_GRCh38DH.20150715.PUR.high_coverage.cram",
    "HG00732": ftp_link+"/PUR/HG00732/high_cov_alignment/HG00732.alt_bwamem_GRCh38DH.20150715.PUR.high_coverage.cram",
    "HG00733": ftp_link+"/PUR/HG00733/high_cov_alignment/HG00733.alt_bwamem_GRCh38DH.20150715.PUR.high_coverage.cram",
    "NA19238": ftp_link+"/YRI/NA19238/high_cov_alignment/NA19238.alt_bwamem_GRCh38DH.20150715.YRI.high_coverage.cram",
    "NA19239": ftp_link+"/YRI/NA19239/high_cov_alignment/NA19239.alt_bwamem_GRCh38DH.20150715.YRI.high_coverage.cram",
    "NA19240": ftp_link+"/YRI/NA19240/high_cov_alignment/NA19240.alt_bwamem_GRCh38DH.20150715.YRI.high_coverage.cram"
    }

    def requires(self):
        return []

    def output(self):
        return luigi.LocalTarget("/pipeline/%s/%s.bam" % (self.sample_name, self.sample_name))

    def run(self):
        dirpath = "/pipeline/%s/" % self.sample_name

        cram_ftp_link = self.samples_ftp[self.sample_name]
        cram_file = dirpath+self.sample_name+".cram"
        bam_file = self.sample_name+".bam"

        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            shutil.rmtree(dirpath)
        os.makedirs(os.path.dirname(dirpath))
        socket.setdefaulttimeout(300)
        urllib.request.urlretrieve(cram_ftp_link, cram_file)

        run_command("samtools view -b -T %s -o %s -@ 32 %s" % (reference_genome, dirpath+bam_file, cram_file))

class PerformAlignment(luigi.Task):
    file_name_1 = luigi.Parameter(default=None)
    file_name_2 = luigi.Parameter(default=None)
    sample_name = luigi.Parameter()
    already_done = luigi.Parameter(default=False)
    train_1000g = luigi.Parameter(default=False)

    def output(self):
        if(self.already_done):
            return luigi.LocalTarget("/pipeline/"+self.sample_name+"/"+self.sample_name+".bam"), luigi.LocalTarget("/pipeline/"+self.sample_name+"/"+self.sample_name+".bam.bai")
        return [luigi.LocalTarget("/pipeline/"+self.sample_name+"/"+self.sample_name+"_preprocessed.bam"), luigi.LocalTarget("/pipeline/"+self.sample_name+"/"+self.sample_name+"_preprocessed.bam.bai")]

    def run(self):
        os.remove("/pipeline/"+self.sample_name+"/"+self.sample_name+".sam")
        os.remove("/pipeline/"+self.sample_name+"/"+self.sample_name+".bam")
        os.remove("/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted.bam")
        os.remove("/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted.bam.bai")
        os.remove("/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted.recal_table")
        os.remove("/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_final.bam")
        os.remove("/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_final.bai")
        os.rename("/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_final_sorted.bam", "/pipeline/"+self.sample_name+"/"+self.sample_name+"_preprocessed.bam")
        os.rename("/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_final_sorted.bam.bai", "/pipeline/"+self.sample_name+"/"+self.sample_name+"_preprocessed.bam.bai")

    def requires(self):
        return IndexFinal(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, already_done=self.already_done, train_1000g=self.train_1000g)



if __name__ == '__main__':
    luigi.run(workers)

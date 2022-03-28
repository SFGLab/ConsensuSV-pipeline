import luigi
import os
import urllib.request 
import shutil
from common import run_command, get_path, get_path_no_ext
from config import reference_genome, no_threads, mem_per_thread
import socket

class MergeFastq(luigi.Task):
    """Class responsible for merging the files in case the sequencing output contains of multiple R1 and R2 files."""
    resources = {"io": 1, "cores": 1}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""

    sample_name = luigi.Parameter()
    """Name of the sample."""
        
    def output(self):
        return [luigi.LocalTarget(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_R1.fastq"), 
        luigi.LocalTarget(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_R2.fastq")]

    def run(self):
        dirpath_main = self.working_dir+"/pipeline/"
        if os.path.exists(dirpath_main) and os.path.isdir(dirpath_main):
            pass
        else:
            os.makedirs(os.path.dirname(dirpath_main))

        dirpath = self.working_dir+"/pipeline/%s/" % self.sample_name
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            shutil.rmtree(dirpath)
        os.makedirs(os.path.dirname(dirpath))

        if(";" in self.file_name_1):
            files = " ".join(self.file_name_1.split(";"))
            if(".gz" in self.file_name_1):
                command_to_use = "zcat"
            else:
                command_to_use = "cat"
            run_command("%s %s > %s" % (command_to_use, files, self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_R1.fastq"))
        else:
            if(".gz" in self.file_name_1):
                run_command("gunzip -c %s > %s" % (self.file_name_1, self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_R1.fastq"))
            else:
                run_command("cp %s %s" % (self.file_name_1, self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_R1.fastq"))

        if(";" in self.file_name_2):
            files = " ".join(self.file_name_2.split(";"))
            if(".gz" in self.file_name_2):
                command_to_use = "zcat"
            else:
                command_to_use = "cat"
            run_command("%s %s > %s" % (command_to_use, files, self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_R2.fastq"))
        else:
            if(".gz" in self.file_name_2):
                run_command("gunzip -c %s > %s" % (self.file_name_2, self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_R2.fastq"))
            else:
                run_command("cp %s %s" % (self.file_name_2, self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_R2.fastq"))

class QCAnalysis(luigi.Task):
    """Class responsible for doing quality control on the merged files."""
    resources = {"io": 1, "cores": 1}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""

    def requires(self):
        return MergeFastq(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return [luigi.LocalTarget(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+'_R1_fastqc.html'), 
        luigi.LocalTarget(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+'_R1_fastqc.html')]

    def run(self):
        self.file_name_1 = self.input()[0].path
        self.file_name_2 = self.input()[1].path

        run_command("fastqc -f fastq -o %s %s" % (self.working_dir+"/pipeline/"+self.sample_name+"/", self.file_name_1))
        run_command("fastqc -f fastq -o %s %s" % (self.working_dir+"/pipeline/"+self.sample_name+"/", self.file_name_2))

class AlignGenome(luigi.Task):
    """Class responsible for aligning the sample to reference genome."""
    resources = {"cores": no_threads}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""

    def requires(self):
        return QCAnalysis(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(self.working_dir+"/pipeline/"+self.sample_name+'/'+self.sample_name+'.sam')

    def run(self):
        command = "bwa mem -v 1 -t %s -B 4 -O 6 -E 1 -M -R \"@RG\\tID:SRR\\tLB:LIB_1\\tSM:SAMPLE_1\\tPL:ILLUMINA\" %s %s %s > %s" % \
        (no_threads, reference_genome, self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_R1.fastq", self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_R2.fastq", self.working_dir+"/pipeline/"+self.sample_name+'/'+self.sample_name+'.sam')

        run_command(command)

class ConvertToBam(luigi.Task):
    """Class responsible for converting the aligned sample to bam file format."""
    resources = {"cores": no_threads}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""

    def requires(self):
        return AlignGenome(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+".bam")

    def run(self):
        full_path_output = get_path_no_ext(self.input().path)+".bam"
        run_command("samtools view -S -b -o %s -@ %s %s" % (full_path_output, no_threads, self.input().path,))

class SortBam(luigi.Task):
    """Class responsible for sorting the bam file."""
    resources = {"io": 1, "cores": no_threads}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""

    def requires(self):
        return ConvertToBam(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+"_sorted.bam")

    def run(self):
        full_path_output = get_path_no_ext(self.input().path)+"_sorted.bam"
        run_command("samtools sort -o %s -T %s -@ %s -m %s %s" % (full_path_output, self.input().path, no_threads, mem_per_thread, self.input().path))

class IndexBam(luigi.Task):
    """Class responsible for indexing the sorted bam file."""
    resources = {"cores": 1}
    """Resources used by the task."""
    
    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""

    def requires(self):
        return SortBam(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(self.input().path+".bai")

    def run(self):
        run_command("samtools index -@ %s %s " % (no_threads, self.input().path))

class MarkDuplicates(luigi.Task):
    """Class responsible for marking duplicates using bammarkduplicates. Indexes the output as well."""
    resources = {"cores": 1}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""

    def requires(self):
        return IndexBam(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path, 2)+"_dp.bam")

    def run(self):
        input_file = get_path_no_ext(self.input().path, 2)+".bam"
        output_file = get_path_no_ext(self.input().path, 2)+"_dp.bam"
        run_command("bammarkduplicates I=%s O=%s index=1 rmdup=1" % (input_file, output_file))
        run_command("samtools index -@ %s %s " % (no_threads, output_file))

class BaseRecalibrator(luigi.Task):
    """Class responsible for base recalibration using gatk."""
    resources = {"cores": 1}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""

    known_sites = "/tools/ALL_20141222.dbSNP142_human_GRCh38.snps.vcf.gz"

    def requires(self):
        return MarkDuplicates(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+".recal_table")

    def run(self):
        input_file = get_path_no_ext(self.input().path)+".bam"
        recal_table = get_path_no_ext(input_file)+".recal_table"

        run_command("gatk BaseRecalibrator -R %s -O %s -I %s -known-sites %s" % (reference_genome, recal_table, input_file, self.known_sites))

class ApplyBQSR(luigi.Task):
    """Class responsible for applying BQSR (Base Quality Score recalibration) using gatk."""
    resources = {"cores": 1}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""

    def requires(self):
        return BaseRecalibrator(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+"_final.bam")

    def run(self):
        recal_table = self.input().path
        input_file = get_path_no_ext(recal_table)+".bam"
        output_file = get_path_no_ext(recal_table)+"_final.bam"

        run_command("gatk ApplyBQSR -R %s -O %s -I %s -bqsr-recal-file %s" % (reference_genome, output_file, input_file, recal_table))

class SortFinal(luigi.Task):
    """Class responsible for final sorting."""
    resources = {"io": 1, "cores": no_threads}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""
    train_1000g = luigi.BoolParameter(default=False)
    """Information whether the current task is part of 1000G benchmarking pipeline."""

    def requires(self):
        if(self.train_1000g):
            return Get1000G(working_dir=self.working_dir)
        else:        
            return ApplyBQSR(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        if(self.train_1000g):
            return luigi.LocalTarget((self.working_dir+"/pipeline/%s/%s" % (self.sample_name, self.sample_name))+"_sorted.bam")
        else:
            return luigi.LocalTarget(get_path_no_ext(self.input().path)+"_sorted.bam")

    def run(self):
        if(self.train_1000g):
            input_file = self.working_dir+"/pipeline/%s/%s.bam" % (self.sample_name, self.sample_name)
            output_file = self.working_dir+"/pipeline/%s/%s_sorted.bam" % (self.sample_name, self.sample_name)
        else:
            input_file = self.input().path
            output_file = get_path_no_ext(self.input().path)+"_sorted.bam"

        run_command("samtools sort -o %s -T %s -@ %s -m %s %s" % (output_file, get_path(input_file), no_threads, mem_per_thread, input_file))

class IndexFinal(luigi.Task):
    """Class responsible for final indexing."""
    resources = {"cores": no_threads}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter()
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter()
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""
    train_1000g = luigi.BoolParameter(default=False)
    """Information whether the current task is part of 1000G benchmarking pipeline."""

    def requires(self):
        return SortFinal(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input().path)+".bam.bai")

    def run(self):
        if(self.train_1000g):
            input_file = self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted.bam"
        else:
            input_file = self.input().path
        run_command("samtools index -@ %s %s" % (no_threads, input_file))

class Get1000G(luigi.Task):
    """Class responsible for getting 9 high-quality NYGC from the ftp servers. Because of the FTP server connection issues, it is done sequentially."""
    resources = {"cores": no_threads}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

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
        return [luigi.LocalTarget(self.working_dir+"/pipeline/%s/%s.bam" % (sample, sample)) for sample in self.samples_ftp]

    def run(self):
        for sample, cram_ftp_link in self.samples_ftp.items():
            
            dirpath = self.working_dir+"/pipeline/%s/" % sample
            if not(os.path.exists(dirpath) and os.path.isdir(dirpath)):
                os.makedirs(os.path.dirname(dirpath))

            cram_file = dirpath+sample+".cram"
            bam_file = dirpath+sample+".bam"
            if not(os.path.isfile(cram_file)):                
                socket.setdefaulttimeout(3600)
                urllib.request.urlretrieve(cram_ftp_link, cram_file)
            if not(os.path.isfile(bam_file)):
                run_command("samtools view -b -T %s -o %s -@ %s %s" % (reference_genome, bam_file, no_threads, cram_file))

class PerformAlignment(luigi.Task):
    """Class ending the alignment step, cleaning up the intermediate files, leaving only final, sorted and indexed alignemnt file."""
    resources = {"io": 1, "cores": 1}
    """Resources used by the task."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""

    file_name_1 = luigi.Parameter(default=None)
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter(default=None)
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""
    train_1000g = luigi.BoolParameter(default=False)
    """Information whether the current task is part of 1000G benchmarking pipeline."""

    def output(self):
        return [luigi.LocalTarget(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_preprocessed.bam"), luigi.LocalTarget(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_preprocessed.bam.bai")]

    def run(self):
        if(self.train_1000g):
            os.rename(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted.bam", self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_preprocessed.bam")
            os.rename(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted.bam.bai", self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_preprocessed.bam.bai")
        else:
            os.remove(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+".sam")
            os.remove(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+".bam")
            os.remove(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted.bam")
            os.remove(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted.bam.bai")
            os.remove(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_dp.bam")
            os.remove(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_dp.bam.bai")
            os.remove(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_dp.recal_table")
            os.remove(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_dp_final.bam")
            os.remove(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_dp_final.bai")
            os.rename(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_dp_final_sorted.bam", self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_preprocessed.bam")
            os.rename(self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_sorted_dp_final_sorted.bam.bai", self.working_dir+"/pipeline/"+self.sample_name+"/"+self.sample_name+"_preprocessed.bam.bai")

    def requires(self):
        return IndexFinal(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)



if __name__ == '__main__':
    luigi.run(workers)

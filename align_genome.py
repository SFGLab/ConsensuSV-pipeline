import luigi
import subprocess
import os

reference_genome = "/tools/GRCh38_full_analysis_set_plus_decoy_hla.fa"
debug = 1

def run_command(command):
        if(debug):
            print("___COMMAND: " + command)
        result = subprocess.getoutput(command)
        if(debug):
            print("___OUTPUT:" + result)

class AlignGenome(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget("/pipeline/"+self.output_file_name+'.sam')

    def run(self):
        command = "bwa mem -t 1 -B 4 -O 6 -E 1 -M -R \"@RG\\tID:SRR\\tLB:LIB_1\\tSM:SAMPLE_1\\tPL:ILLUMINA\" %s %s %s > %s" % \
        (reference_genome, self.file_name_1, self.file_name_2, "/pipeline/"+self.output_file_name+'.sam')

        run_command(command)

class ConvertToBam(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return AlignGenome(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(self.input().path.split(".")[0]+".bam")

    def run(self):
        full_path_output = self.input().path.split(".")[0]+".bam"
        run_command("samtools view -S -b %s > %s" % (self.input().path, full_path_output))

class SortBam(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return ConvertToBam(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(self.input().path.split(".")[0]+"_sorted.bam")

    def run(self):
        full_path_output = self.input().path.split(".")[0]+"_sorted.bam"
        run_command("samtools sort %s > %s" % (self.input().path, full_path_output))

class IndexBam(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return SortBam(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(self.input().path+".bai")

    def run(self):
        run_command("samtools index %s" % self.input().path)

class BaseRecalibrator(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    known_sites = "/tools/ALL_20141222.dbSNP142_human_GRCh38.snps.vcf.gz"

    def requires(self):
        return IndexBam(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(self.input().path.split(".")[0]+".recal_table")

    def run(self):
        input_file = self.input().path.split(".")[0]+".bam"
        recal_table = input_file.split(".")[0]+".recal_table"

        run_command("gatk BaseRecalibrator -R %s -O %s -I %s -known-sites %s" % (reference_genome, recal_table, input_file, self.known_sites))

class ApplyBQSR(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return BaseRecalibrator(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(self.input().path.split(".")[0]+"_final.bam")

    def run(self):
        recal_table = self.input().path
        input_file = recal_table.split(".")[0]+".bam"
        output_file = recal_table.split(".")[0]+"_final.bam"

        run_command("gatk ApplyBQSR -R %s -O %s -I %s -bqsr-recal-file %s" % (reference_genome, output_file, input_file, recal_table))

class SortFinal(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return ApplyBQSR(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(self.input().path.split(".")[0]+"_sorted.bam")

    def run(self):
        input_file = self.input().path.split(".")[0]+"_sorted.bam"
        output_file = self.input().path.split(".")[0]+"_sorted.bam"

        run_command("samtools sort %s > %s" % (self.input().path, output_file))

class IndexFinal(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return SortFinal(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(self.input().path.split(".")[0]+".bam.bai")

    def run(self):
        run_command("samtools index %s" % self.input().path)

class PerformAlignment(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def output(self):
        return [luigi.LocalTarget("/pipeline/"+self.output_file_name+"_preprocessed.bam"), luigi.LocalTarget("/pipeline/"+self.output_file_name+"_preprocessed.bam.bai")]

    def run(self):
        os.remove("/pipeline/"+self.output_file_name+".sam")
        os.remove("/pipeline/"+self.output_file_name+".bam")
        os.remove("/pipeline/"+self.output_file_name+"_sorted.bam")
        os.remove("/pipeline/"+self.output_file_name+"_sorted.bam.bai")
        os.remove("/pipeline/"+self.output_file_name+"_sorted.recal_table")
        os.remove("/pipeline/"+self.output_file_name+"_sorted_final.bam")
        os.remove("/pipeline/"+self.output_file_name+"_sorted_final.bai")
        os.rename("/pipeline/"+self.output_file_name+"_sorted_final_sorted.bam", "/pipeline/"+self.output_file_name+"_preprocessed.bam")
        os.rename("/pipeline/"+self.output_file_name+"_sorted_final_sorted.bam.bai", "/pipeline/"+self.output_file_name+"_preprocessed.bam.bai")

    def requires(self):
        return IndexFinal(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

class SNPCalling(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(self.input()[0].path.split(".")[0]+"_SNPs.vcf")

    def run(self):
        input_file = self.input()[0].path
        inter_file = self.input()[0].path.split(".")[0]+"_SNPs.bcf"
        output_file = self.input()[0].path.split(".")[0]+"_SNPs.vcf"

        run_command("bcftools mpileup -Ou -f %s %s | bcftools call -mv -Ob -o %s && bcftools view -i '%%QUAL>=20' %s > %s" % (reference_genome, input_file, inter_file, inter_file, output_file))

class SVDelly(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(self.input()[0].path.split(".")[0]+"_delly.vcf")

    def run(self):
        input_file = self.input()[0].path
        inter_file = self.input()[0].path.split(".")[0]+"_delly.bcf"
        output_file = self.input()[0].path.split(".")[0]+"_delly.vcf"

        run_command("delly_v0.8.7_linux_x86_64bit call -o %s -g %s %s && bcftools view %s > %s" % (inter_file, reference_genome, input_file, inter_file, output_file))

class SVDelly(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(self.input()[0].path.split(".")[0]+"_delly.vcf")

    def run(self):
        input_file = self.input()[0].path
        inter_file = self.input()[0].path.split(".")[0]+"_breakdancer.cfg"
        output_file = self.input()[0].path.split(".")[0]+"_breakdancer.vcf"

        run_command("bam2cfg.pl %s > %s" % (input_file, config_file))
        run_command("breakdancer-max %s > %s" % (config_file, inter_file))
        run_command("python breakdancer2vcf.py <%s > %s" % (inter_file, output_file))

class CallVariants(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return [SNPCalling(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name),
        SVDelly(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)]

    def output(self):
        return luigi.LocalTarget(self.input()[0].path.split(".")[0]+"_SNPs.vcf")

    def run(self):
        os.remove(self.input()[0].path.split(".")[0]+".bcf")
        os.remove(self.input()[1].path.split(".")[0]+".bcf")
        os.remove(self.input()[1].path.split(".")[0]+".bcf.csi")

if __name__ == '__main__':
    luigi.run()

# INSTALLED: SNPs, BreakDancer, delly
# TODO: CNVnator, breakseq, lumpy, Manta (run on breakseq conda), tardis, svelter (run on breakseq conda), whamg, novoBreak
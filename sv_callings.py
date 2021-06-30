from align_genome import PerformAlignment
from common import reference_genome, debug, run_command, get_path_no_ext
import luigi
import os

class SNPCalling(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_SNPs.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        inter_file = input_file_no_ext+"_SNPs.bcf"
        output_file = input_file_no_ext+"_SNPs.vcf"

        run_command("bcftools mpileup -Ou -f %s %s | bcftools call -mv -Ob -o %s && bcftools view -i '%%QUAL>=20' %s > %s" % (reference_genome, input_file, inter_file, inter_file, output_file))

        os.remove(inter_file)

class SVDelly(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_delly.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        inter_file = input_file_no_ext+"_delly.bcf"
        output_file = input_file_no_ext+"_delly.vcf"

        run_command("delly_v0.8.7_linux_x86_64bit call -o %s -g %s %s && bcftools view %s > %s" % (inter_file, reference_genome, input_file, inter_file, output_file))
        os.remove(inter_file)
        os.remove(inter_file+".csi")

class SVBreakdancer(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_breakdancer.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        config_file = input_file_no_ext+"_breakdancer.cfg"
        inter_file = input_file_no_ext+"_breakdancer.calls"
        output_file = input_file_no_ext+"_breakdancer.vcf"

        run_command("bam2cfg.pl %s > %s" % (input_file, config_file))
        run_command("breakdancer-max %s > %s" % (config_file, inter_file))
        run_command("python /tools/breakdancer-master/bin/breakdancer2vcf.py <%s > %s" % (inter_file, output_file), "breakseq")

        os.remove(config_file)
        os.remove(inter_file)

class SVTardis(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_tardis.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        sonic_file = "/tools/GRCh38_1kg.sonic"
        output_file = input_file_no_ext+"_tardis.vcf"

        run_command("tardis -i %s --ref %s --sonic %s --out %s --first-chr 0 --last-chr 24" % (input_file, reference_genome, sonic_file, output_file))
        

class SVNovoBreak(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_novoBreak.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        novoBreak_control = input_file_no_ext+"_novoBreakControl.bam"
        output_file = input_file_no_ext+"_novoBreak.vcf"

        run_command("samtools view -H %s | samtools view -bh > %s" % (input_file, novoBreak_control))
        run_command("samtools index %s" % novoBreak_control)
        run_command("run_novoBreak.sh /tools/nb_distribution/ %s %s %s 4 /pipeline/%s" % (reference_genome, input_file, novoBreak_control, self.output_file_name))
        run_command("vcftools --vcf /pipeline/%s/novoBreak.pass.flt.vcf --out %s --minQ 50 --recode --recode-INFO-all" % (self.output_file_name, output_file))

        os.remove(novoBreak_control)

class SVCNVNator(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_cnvnator.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        root_file = input_file_no_ext+".root"
        inter_file = get_path_no_ext(self.input()[0].path)+".cnvout"
        output_file = input_file_no_ext+"_cnvnator.vcf"

        run_command("cnvnator -root %s -tree %s -chrom $(seq 1 22) X Y" % (root_file, input_file))
        run_command("cnvnator -root %s -his 1000 -fasta %s" % (root_file, reference_genome))
        run_command("cnvnator -root %s -stat 1000" % (root_file))
        run_command("cnvnator -root %s -partition 1000" % (root_file))
        run_command("cnvnator -root %s -call 1000 > %s" % (root_file, inter_file))
        run_command("cnvnator2VCF.pl -prefix %s -reference GRCh38 %s /pipeline/ > %s" % (self.output_file_name, inter_file, output_file))

        os.remove(inter_file)
        os.remove(root_file)


class CallVariants(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    output_file_name = luigi.Parameter()

    def requires(self):
        return [SNPCalling(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name),
        SVDelly(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name),
        SVBreakdancer(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name),
        SVTardis(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name),
        SVNovoBreak(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name),
        SVCNVNator(file_name_1=self.file_name_1, file_name_2=self.file_name_2, output_file_name=self.output_file_name)
        ]

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_SNPs.vcf")

    def run(self):
        pass

if __name__ == '__main__':
    luigi.run()

# INSTALLED: SNPs, BreakDancer, delly, tardis, novoBreak
# TODO: CNVnator, breakseq, lumpy, Manta (run on breakseq conda), svelter (run on breakseq conda), whamg
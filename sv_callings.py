from align_genome import PerformAlignment
from common import reference_genome, debug, run_command, get_path_no_ext, all_chromosomes
import luigi
import os
import shutil

class SNPCalling(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

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
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

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
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

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
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_tardis.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        sonic_file = "/tools/GRCh38_1kg.sonic"
        output_file = input_file_no_ext+"_tardis"
        log_file = output_file+"-tardis.log"

        run_command("tardis -i %s --ref %s --sonic %s --out %s --first-chr 0 --last-chr 24" % (input_file, reference_genome, sonic_file, output_file))
        os.remove(log_file)
        
class SVNovoBreak(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_novoBreak.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        novoBreak_control = input_file_no_ext+"_novoBreakControl.bam"
        output_file = input_file_no_ext+"_novoBreak.vcf"
        working_dir = "/pipeline/%s_novoBreak" % self.sample_name

        run_command("samtools view -H %s | samtools view -bh > %s" % (input_file, novoBreak_control))
        run_command("samtools index %s" % novoBreak_control)
        run_command("run_novoBreak.sh /tools/nb_distribution/ %s %s %s 4 %s" % (reference_genome, input_file, novoBreak_control, working_dir))
        run_command("vcftools --vcf /pipeline/%s_novoBreak/novoBreak.pass.flt.vcf --out %s --minQ 50 --recode --recode-INFO-all" % (self.sample_name, output_file), return_output=True)

        os.rename(output_file+".recode.vcf", output_file)
        os.remove(novoBreak_control)
        os.remove(novoBreak_control+".bai")
        shutil.rmtree(working_dir)

class SVCNVNator(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

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
        run_command("cnvnator2VCF.pl -prefix %s -reference GRCh38 %s /pipeline/ > %s" % (self.sample_name, inter_file, output_file))

        os.remove(inter_file)
        os.remove(root_file)

class SVBreakSeq(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_breakseq.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        output_file = input_file_no_ext+"_breakseq.vcf"
        working_dir = "/pipeline/"+self.sample_name+"_breakseq"

        run_command("run_breakseq2.py --reference %s --bams %s --work %s --bwa %s --samtools %s --bplib_gff %s --nthreads 4 --sample %s" % (reference_genome, input_file, \
        working_dir, "/tools/bwa-0.7.17/bwa", "/tools/samtools-0.1.19/samtools", "/tools/breakseq2_bplib_20150129_chr.gff", self.sample_name), "breakseq")

        run_command("gunzip %s/breakseq.vcf.gz" % working_dir)
        os.rename("%s/breakseq.vcf" % working_dir, output_file)
        shutil.rmtree(working_dir)

class SVManta(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_manta.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        run_command("gunzip %s/results/variants/diploidSV.vcf.gz" % working_dir)
        input_file = self.input()[0].path
        output_file = input_file_no_ext+"_manta.vcf"
        working_dir = "/pipeline/"+self.sample_name+"_Manta"

        run_command("configManta.py --bam %s --referenceFasta %s --runDir %s" % (input_file, reference_genome, working_dir), "breakseq")
        run_command("%s/runWorkflow.py" % working_dir, "breakseq")
        run_command("gunzip %s/results/variants/diploidSV.vcf.gz" % working_dir)
        os.rename("%s/results/variants/diploidSV.vcf" % working_dir, output_file)
        shutil.rmtree(working_dir)

class SVLumpy(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_lumpy.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        discordants_file_unsorted = input_file_no_ext+".discordants.unsorted.bam"
        discordants_file = input_file_no_ext+".discordants.bam"
        splitters_file_unsorted = input_file_no_ext+".splitters.unsorted.bam"
        splitters_file = input_file_no_ext+".splitters.bam"
        output_file = input_file_no_ext+"_lumpy.vcf"
        working_dir = "/pipeline/"+self.sample_name+"_lumpy"

        run_command("samtools view -b -F 1294 %s > %s" % (input_file, discordants_file_unsorted))
        run_command("samtools sort -o %s %s" % (discordants_file, discordants_file_unsorted))
        run_command("samtools view -h %s | /tools/lumpy-sv/scripts/extractSplitReads_BwaMem -i stdin | samtools view -Sb - > %s" % (input_file, splitters_file_unsorted))
        run_command("samtools sort -o %s %s" % (splitters_file, splitters_file_unsorted))
        run_command("lumpyexpress -B %s -S %s -D %s -R %s -T %s -o %s" % (input_file, splitters_file, discordants_file, reference_genome, working_dir, output_file), "breakseq")

        os.remove(discordants_file_unsorted)
        os.remove(discordants_file)
        os.remove(splitters_file_unsorted)
        os.remove(splitters_file)

class SVWhamg(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_whamg.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        output_file = input_file_no_ext+"_whamg.vcf"
        error_file = input_file_no_ext+"_whamg.err"
        filter_script = "/tools/wham/utils/filtWhamG.pl"
        run_command("whamg -c %s -a %s -f %s | perl %s > %s  2> %s" % (all_chromosomes, reference_genome, input_file, filter_script, output_file, error_file))

        os.remove(error_file)

class SVSvelter(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return PerformAlignment(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_svelter.vcf")

    def run(self):
        input_file_no_ext = get_path_no_ext(self.input()[0].path)
        input_file = self.input()[0].path
        output_file = input_file_no_ext+"_svelter.vcf"
        support_dir = "/tools/svelter/Support/GRCh38/"

        run_command("svelter.py Setup --reference %s --workdir %s --support %s" % (reference_genome, work_dir, support_dir), "breakseq")
        run_command("svelter.py --sample %s --workdir %s --chromosome %s" % (input_file, work_dir, all_chromosomes), "breakseq")

class CallVariants(luigi.Task):
    file_name_1 = luigi.Parameter()
    file_name_2 = luigi.Parameter()
    sample_name = luigi.Parameter()

    def requires(self):
        return [SNPCalling(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name),
        SVDelly(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name),
        SVBreakdancer(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name),
        SVTardis(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name),
        SVNovoBreak(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name),
        SVCNVNator(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name),
        SVBreakSeq(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name),
        SVManta(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name),
        SVLumpy(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name),
        SVWhamg(file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name)
        ]

    def output(self):
        return luigi.LocalTarget(get_path_no_ext(self.input()[0].path)+"_SNPs.vcf")

    def run(self):
        pass

if __name__ == '__main__':
    luigi.run()

# INSTALLED: SNPs, BreakDancer, delly, tardis, novoBreak, CNVnator, breakseq, Manta, lumpy, svelter
from align_genome import PerformAlignment
from common import run_command, get_path, get_path
from config import reference_genome, no_threads, all_chromosomes, mem_per_thread
import luigi
import os
import shutil

class SNPCalling(luigi.Task):
    """Class responsible for SNP calling using bcftools."""
    resources = {"cores": 1}
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"SNPs.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        inter_file = input_file_path+"SNPs.bcf"
        output_file = input_file_path+"SNPs.vcf"

        run_command("bcftools mpileup -Ou -f %s %s | bcftools call --skip-variants indels -mv -Ob -o %s && bcftools view -i '%%QUAL>=20' %s > %s" % (reference_genome, input_file, inter_file, inter_file, output_file))

        os.remove(inter_file)

class IndelCalling(luigi.Task):
    """Class responsible for Indel calling using bcftools."""
    resources = {"cores": 1}
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"Indels.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        inter_file = input_file_path+"Indels.bcf"
        output_file = input_file_path+"Indels.vcf"

        run_command("bcftools mpileup -Ou -f %s %s | bcftools call --skip-variants snps -mv -Ob -o %s && bcftools view -i '%%QUAL>=20' %s > %s" % (reference_genome, input_file, inter_file, inter_file, output_file))

        os.remove(inter_file)

class SVDelly(luigi.Task):
    """Class responsible for SV calling using Delly."""
    resources = {"cores": 1}
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"delly.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        inter_file = input_file_path+"delly.bcf"
        output_file = input_file_path+"delly.vcf"

        run_command("delly_v0.8.7_linux_x86_64bit call -o %s -g %s %s && bcftools view %s > %s" % (inter_file, reference_genome, input_file, inter_file, output_file))
        os.remove(inter_file)
        os.remove(inter_file+".csi")

class SVBreakdancer(luigi.Task):
    """Class responsible for SV calling using Breakdancer."""
    resources = {"cores": 1}
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"breakdancer.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        config_file = input_file_path+"breakdancer.cfg"
        inter_file = input_file_path+"breakdancer.calls"
        output_file = input_file_path+"breakdancer.vcf"

        run_command("bam2cfg.pl %s > %s" % (input_file, config_file))
        run_command("breakdancer-max %s > %s" % (config_file, inter_file))
        run_command("python /tools/breakdancer-master/bin/breakdancer2vcf.py <%s > %s" % (inter_file, output_file), "breakseq")

        os.remove(config_file)
        os.remove(inter_file)

class SVTardis(luigi.Task):
    """Class responsible for SV calling using Tardis."""
    resources = {"cores": 1}
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"tardis.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        sonic_file = "/tools/GRCh38_1kg.sonic"
        output_file = input_file_path+"tardis"
        log_file = output_file+"-tardis.log"

        run_command("tardis -i %s --ref %s --sonic %s --out %s --first-chr 0 --last-chr 24" % (input_file, reference_genome, sonic_file, output_file))
        os.remove(log_file)
        
class SVNovoBreak(luigi.Task):
    """Class responsible for SV calling using novoBreak. It is disabled in default run because of its computational time."""
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"novoBreak.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        novoBreak_control = input_file_path+"novoBreakControl.bam"
        output_file = input_file_path+"novoBreak.vcf"
        working_dir = self.working_dir+"/pipeline/%s/novoBreak" % self.sample_name

        run_command("samtools view -H %s | samtools view -bh > %s" % (input_file, novoBreak_control))
        run_command("samtools index %s" % novoBreak_control)
        run_command("run_novoBreak.sh /tools/nb_distribution/ %s %s %s 4 %s" % (reference_genome, input_file, novoBreak_control, working_dir))
        run_command("vcftools --vcf %s/pipeline/%s/novoBreak/novoBreak.pass.flt.vcf --out %s --minQ 50 --recode --recode-INFO-all" % (self.working_dir, self.sample_name, output_file))

        os.rename(output_file+".recode.vcf", output_file)
        os.remove(novoBreak_control)
        os.remove(novoBreak_control+".bai")
        shutil.rmtree(working_dir)

class SVCNVNator(luigi.Task):
    """Class responsible for SV calling using CNVNator."""
    resources = {"cores": 1} # might take more, but for short time
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"cnvnator.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        root_file = input_file_path+"cnv.root"
        inter_file = get_path(self.input()[0].path)+"cnv.cnvout"
        output_file = input_file_path+"cnvnator.vcf"

        run_command("cnvnator -root %s -tree %s -chrom $(seq 1 22) X Y" % (root_file, input_file))
        run_command("cnvnator -root %s -his 1000 -fasta %s" % (root_file, reference_genome))
        run_command("cnvnator -root %s -stat 1000" % (root_file))
        run_command("cnvnator -root %s -partition 1000" % (root_file))
        run_command("cnvnator -root %s -call 1000 > %s" % (root_file, inter_file))
        run_command("cnvnator2VCF.pl -prefix %s -reference GRCh38 %s %s/pipeline/%s/ > %s" % (self.sample_name, inter_file, self.working_dir, self.sample_name, output_file))

        os.remove(inter_file)
        os.remove(root_file)

class SVBreakSeq(luigi.Task):
    """Class responsible for SV calling using BreakSeq."""
    resources = {"io": 1, "cores": no_threads}
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"breakseq.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        output_file = input_file_path+"breakseq.vcf"
        working_dir = self.working_dir+"/pipeline/"+self.sample_name+"/breakseq"

        run_command("run_breakseq2.py --reference %s --bams %s --work %s --bwa %s --samtools %s --bplib_gff %s --nthreads %s --sample %s --chromosomes %s" % (reference_genome, input_file, \
        working_dir, "/tools/bwa-0.7.17/bwa", "/tools/samtools-0.1.19/samtools", "/tools/breakseq2_bplib_20150129_chr.gff", no_threads, self.sample_name, " ".join(all_chromosomes.split(","))), "breakseq")

        run_command("gunzip %s/breakseq.vcf.gz" % working_dir)
        os.rename("%s/breakseq.vcf" % working_dir, output_file)
        shutil.rmtree(working_dir)

class SVManta(luigi.Task):
    """Class responsible for SV calling using Manta."""
    resources = {"io": 1, "cores": no_threads*2}
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"manta.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        output_file = input_file_path+"manta.vcf"
        working_dir = self.working_dir+"/pipeline/"+self.sample_name+"/Manta"

        run_command("configManta.py --bam %s --referenceFasta %s --runDir %s" % (input_file, reference_genome, working_dir), "breakseq")
        run_command("%s/runWorkflow.py -j %s -g %s" % (working_dir, no_threads*2, str(int(mem_per_thread.split("G")[0])*4)), "breakseq")
        run_command("gunzip %s/results/variants/diploidSV.vcf.gz" % working_dir)
        os.rename("%s/results/variants/diploidSV.vcf" % working_dir, output_file)
        shutil.rmtree(working_dir)

class SVLumpy(luigi.Task):
    """Class responsible for SV calling using Lumpy."""
    resources = {"io": 1, "cores": no_threads}
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"lumpy.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        discordants_file_unsorted = input_file_path+"lumpy.discordants.unsorted.bam"
        discordants_file = input_file_path+"lumpy.discordants.bam"
        splitters_file_unsorted = input_file_path+"lumpy.splitters.unsorted.bam"
        splitters_file = input_file_path+"lumpy.splitters.bam"
        output_file = input_file_path+"lumpy.vcf"
        working_dir = self.working_dir+"/pipeline/"+self.sample_name+"/lumpy"

        run_command("samtools view -b -F 1294 -@ %s %s > %s" % (no_threads, input_file, discordants_file_unsorted))
        run_command("samtools sort -o %s -@ %s -m %s %s" % (discordants_file, no_threads, mem_per_thread, discordants_file_unsorted))
        run_command("samtools view -h %s | /tools/lumpy-sv/scripts/extractSplitReads_BwaMem -i stdin | samtools view -Sb - > %s" % (input_file, splitters_file_unsorted))
        run_command("samtools sort -o %s -@ %s -m %s %s" % (splitters_file, no_threads, mem_per_thread, splitters_file_unsorted))
        run_command("lumpyexpress -B %s -S %s -D %s -R %s -T %s -o %s" % (input_file, splitters_file, discordants_file, reference_genome, working_dir, output_file), "breakseq")

        os.remove(discordants_file_unsorted)
        os.remove(discordants_file)
        os.remove(splitters_file_unsorted)
        os.remove(splitters_file)

class SVWhamg(luigi.Task):
    """Class responsible for SV calling using Whamg."""
    resources = {"cores": 1}
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"whamg.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        output_file = input_file_path+"whamg.vcf"
        error_file = input_file_path+"whamg.err"
        filter_script = "/tools/wham/utils/filtWhamG.pl"
        run_command("whamg -c %s -a %s -f %s | perl %s > %s  2> %s" % (all_chromosomes, reference_genome, input_file, filter_script, output_file, error_file))

        os.remove(error_file)

class SVSvelter(luigi.Task):
    """Class responsible for SV calling using Svelter."""
    resources = {"cores": 1}
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

    def requires(self):
        return PerformAlignment(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)

    def output(self):
        return luigi.LocalTarget(get_path(self.input()[0].path)+"_svelter.vcf")

    def run(self):
        input_file_path = get_path(self.input()[0].path)
        input_file = self.input()[0].path
        output_file = input_file_path+"svelter.vcf"
        support_dir = "/tools/svelter/Support/GRCh38/"

        run_command("svelter.py Setup --reference %s --workdir %s --support %s" % (reference_genome, work_dir, support_dir), "breakseq")
        run_command("svelter.py --sample %s --workdir %s --chromosome %s" % (input_file, work_dir, all_chromosomes), "breakseq")

class CallVariants(luigi.Task):
    """Class responsible for calling variants using various methods."""
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

    def requires(self):
        return [SNPCalling(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g),
        IndelCalling(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g),
        SVDelly(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g),
        SVBreakdancer(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g),
        SVTardis(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g),
        SVCNVNator(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g),
        SVBreakSeq(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g),
        SVManta(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g),
        SVLumpy(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g),
        SVWhamg(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=self.train_1000g)
        ]

    def output(self):
        return [luigi.LocalTarget(get_path(self.input()[0].path)+"SNPs.vcf"),
        luigi.LocalTarget(get_path(self.input()[0].path)+"Indels.vcf"),
        luigi.LocalTarget(get_path(self.input()[0].path)+"delly.vcf"),
        luigi.LocalTarget(get_path(self.input()[0].path)+"breakdancer.vcf"),
        luigi.LocalTarget(get_path(self.input()[0].path)+"tardis.vcf"),
        luigi.LocalTarget(get_path(self.input()[0].path)+"cnvnator.vcf"),
        luigi.LocalTarget(get_path(self.input()[0].path)+"breakseq.vcf"),
        luigi.LocalTarget(get_path(self.input()[0].path)+"manta.vcf"),
        luigi.LocalTarget(get_path(self.input()[0].path)+"lumpy.vcf"),
        luigi.LocalTarget(get_path(self.input()[0].path)+"whamg.vcf")]

    def run(self):
        pass

if __name__ == '__main__':
    luigi.run()

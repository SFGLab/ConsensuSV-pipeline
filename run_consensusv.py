from sv_callings import CallVariants
from common import run_command
import luigi
import os
import shutil
from datetime import datetime

class Train1000G(luigi.Task):
    """Class for running ConsensuSV training on 6 high-quality samples from NYGC."""

    working_dir = luigi.Parameter()
    """Working directory of the task."""
    def requires(self):
        return [CallVariants(working_dir=self.working_dir, sample_name="HG00512", train_1000g=True),
        CallVariants(working_dir=self.working_dir, sample_name="HG00513", train_1000g=True),
        CallVariants(working_dir=self.working_dir, sample_name="HG00514", train_1000g=True),
        CallVariants(working_dir=self.working_dir, sample_name="HG00731", train_1000g=True),
        CallVariants(working_dir=self.working_dir, sample_name="HG00732", train_1000g=True),
        CallVariants(working_dir=self.working_dir, sample_name="HG00733", train_1000g=True),
        CallVariants(working_dir=self.working_dir, sample_name="NA19238", train_1000g=True),
        CallVariants(working_dir=self.working_dir, sample_name="NA19239", train_1000g=True),
        CallVariants(working_dir=self.working_dir, sample_name="NA19240", train_1000g=True)]

    def output(self):
        return luigi.LocalTarget(self.working_dir+"/1000g_illumina.model")

    def run(self):
        shutil.copyfile("truth_samples/HG00512.vcf", self.working_dir+"/pipeline/HG00512/truth.vcf")
        shutil.copyfile("truth_samples/HG00513.vcf", self.working_dir+"/pipeline/HG00513/truth.vcf")
        shutil.copyfile("truth_samples/HG00514.vcf", self.working_dir+"/pipeline/HG00514/truth.vcf")
        shutil.copyfile("truth_samples/HG00731.vcf", self.working_dir+"/pipeline/HG00731/truth.vcf")
        shutil.copyfile("truth_samples/HG00732.vcf", self.working_dir+"/pipeline/HG00732/truth.vcf")
        shutil.copyfile("truth_samples/HG00733.vcf", self.working_dir+"/pipeline/HG00733/truth.vcf")
        run_command("python -u /tools/ConsensuSV-core/main.py -f %s/pipeline/ -t -s HG00512,HG00513,HG00514,HG00731,HG00732,HG00733 -c breakdancer,breakseq,cnvnator,delly,lumpy,manta,tardis,whamg -mod %s/1000g_illumina.model" % (self.working_dir, self.working_dir))

class Benchmark1000G(luigi.Task):
    """Class for running ConsensuSV and 1000G benchmark on 9 high-quality samples from NYGC."""
    working_dir = luigi.Parameter()
    """Working directory of the task."""
    def requires(self):
        return [Train1000G(working_dir=self.working_dir)]

    def output(self):
        return luigi.LocalTarget("%s/benchmark.txt" % self.working_dir)

    def run(self):
        run_command("python -u /tools/ConsensuSV-core/main.py -f %s/pipeline/ -s HG00512,HG00513,HG00514,HG00731,HG00732,HG00733,NA19238,NA19239,NA19240 -c breakdancer,breakseq,cnvnator,delly,lumpy,manta,tardis,whamg -mod %s/1000g_illumina.model" % (self.working_dir, self.working_dir))
        run_command("python -u /tools/ConsensuSV-core/charles_filter_n.py -s HG00512,HG00513,HG00514,HG00731,HG00732,HG00733,NA19238,NA19239,NA19240 -o %s/output/consensuSV__HG00512.vcf,%s/output/consensuSV__HG00513.vcf,%s/output/consensuSV__HG00514.vcf,%s/output/consensuSV__HG00731.vcf,%s/output/consensuSV__HG00732.vcf,%s/output/consensuSV__HG00733.vcf,%s/output/consensuSV__NA19238.vcf,%s/output/consensuSV__NA19239.vcf,%s/output/consensuSV__NA19240.vcf > %s/benchmark.txt" %(self.working_dir, self.working_dir, self.working_dir, self.working_dir, self.working_dir, self.working_dir, self.working_dir, self.working_dir, self.working_dir, self.working_dir))

class RunConsensuSV(luigi.Task):
    """Class for running ConsensuSV on one sample."""
    working_dir = luigi.Parameter()
    """Working directory of the task."""
    model = luigi.Parameter(default="/tools/ConsensuSV-core/pretrained_1000g_illumina.model")
    """Model used for ML."""
    file_name_1 = luigi.Parameter(default=None)
    """Name of the file containing R1 reads."""
    file_name_2 = luigi.Parameter(default=None)
    """Name of the file containing R2 reads."""
    sample_name = luigi.Parameter()
    """Name of the sample."""

    def requires(self):
        return [CallVariants(working_dir=self.working_dir, file_name_1=self.file_name_1, file_name_2=self.file_name_2, sample_name=self.sample_name, train_1000g=False)]

    def output(self):
        return luigi.LocalTarget("%s/consensuSV__%s.vcf" % (self.working_dir+"/output/", self.sample_name))

    def run(self):
        output_folder = self.working_dir+"/output/"
        
        if not(os.path.exists(output_folder) and os.path.isdir(output_folder)):
            os.makedirs(os.path.dirname(output_folder))

        run_command("python -u /tools/ConsensuSV-core/main.py -of %s/output/ -f %s/pipeline/ -s %s -c breakdancer,breakseq,cnvnator,delly,lumpy,manta,tardis,whamg -mod %s" % (self.working_dir, self.working_dir, self.sample_name, self.model))

class RunCSVFile(luigi.Task):
    """Class for running CSV file into ConsensuSV-pipeline."""

    csv_file = luigi.Parameter(default=None)
    """CSV file that is being processed."""
    working_dir = luigi.Parameter()
    """Working directory of the task."""
    model = luigi.Parameter(default="/tools/ConsensuSV-core/pretrained_1000g_illumina.model")
    """Model used for ML."""

    def requires(self):
        list_of_tasks = []
        with open(self.csv_file) as f:
            for line in f:
                csv_line = line.strip().split(",")
                list_of_tasks.append(RunConsensuSV(working_dir=self.working_dir, model=self.model, file_name_1=csv_line[1], file_name_2=csv_line[2], sample_name=csv_line[0]))
        return list_of_tasks

    def output(self):
        csv_file = luigi.Parameter(default=None)
        list_of_outputs = []
        with open(self.csv_file) as f:
            for line in f:
                csv_line = line.strip().split(",")
                list_of_outputs.append(luigi.LocalTarget("%s/output/consensuSV__%s.vcf" % (self.working_dir, csv_line[0])))
        return list_of_outputs

    def run(self):
        pass

if __name__ == '__main__':
    """Default entrance to the program - prints information about pipeline execution."""

    start_dt = datetime.now()
    """Begining of the execution of the pipeline."""
    print("Execution of the pipeline started at: ", start_dt.strftime("%d/%m/%Y %H:%M:%S"))
    luigi.run()
    end_dt = datetime.now()
    duration_in_s = (end_dt-start_dt).total_seconds()
    print("")
    print("=====================================")
    print("")
    print("Execution of the pipeline started at: ", start_dt.strftime("%d/%m/%Y %H:%M:%S"))
    print("Execution of the pipeline finished at: ", end_dt.strftime("%d/%m/%Y %H:%M:%S"))

    days    = divmod(duration_in_s, 86400)
    hours   = divmod(days[1], 3600)
    minutes = divmod(hours[1], 60)
    seconds = divmod(minutes[1], 1)

    print("Execution of the pipeline lasted: %d days, %d hours, %d minutes and %d seconds" % (days[0], hours[0], minutes[0], seconds[0]))
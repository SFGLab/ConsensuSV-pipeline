# ConsensuSV-pipeline

Table of Contents
=================

* [What is ConsensuSV?](#what-is-consensusv)
* [Citation](#citation)
* [Testing scenarios](#testing-scenarios)
* [Preparation of your samples](#preparation-of-your-samples)
* [Running the pipeline](#running-the-pipeline)
* [Output location](#output-location)
* [Pipeline control webservice](#pipeline-control-webservice)
* [Pipeline details](#pipeline-details)
* [Setup on NVIDIA DGX A100 systems](#setup-on-nvidia-dgx-a100-systems)
* [Benchmark](#benchmark)
## What is ConsensuSV?

Automatised pipeline of ConsensuSV workflow, going from raw sequencing Illumina data (fastq), to output vcf files (structural variants, indels and SNPs). Easy to run, scalable solution for variant discovery.

Docker image: https://hub.docker.com/repository/docker/mateuszchilinski/consensusv-pipeline

## Citation

If you use ConsensuSV in your research, we kidnly as you to cite the following publication:

The citation will be updated upon publication.

```
@article{doi:
author = {Chiliński, Mateusz and Plewczynski, Dariusz},
title = {ConsensuSV},
journal = {},
pages = {},
year = {},
doi = {},
URL = {},
eprint = {}
}
```

## Testing scenarios

For the ease of the verification of the algorithm, we created a few testing scenarios. All of them process data of very shallow sequencing of HG00331 done by 1000 Genomes consortium, that is why the obtained Structural Variants are really low in numbers. The main purpose of those tests, however, are to be sure all the systems work properly before setting up multi-scale analysis.

In all the testing scenarios, you need to get into the docker container having downloaded it using:

```shell
docker run -p 8082:8082 -it mateuszchilinski/consensusv-pipeline:latest
```

First testing scenario uses only two fastq files of HG00331:

```shell
./test_run_fast.sh
```

Second testing scenario combines four fastq files of HG00331 (which are specified in samples.csv file):

```shell
./test_run_csv.sh
```

The last testing, or rather training example reproduces the whole procedure required for the training of the model. The pretrained model is included with the software (for 8 SV callers that are used), however one can pretrain it themselves using command:

```shell
./train_on_1000g.sh
```

Bear in mind that this command is very time consuming - as it is downloading 9 super high-quality samples from HGSV (coverage x90; the download because of the server issues is not paralleled). However, as we believe all the results and models should be easily reproductable, we included it as well in the pipeline.

## Preparation of your samples

Since the algorithm is easy-to-run, the preparation of the sample is minimal. The algorithm works with raw fastq files, and a csv file containing all the sample information is needed. The columns in the file are as follow:

* name of the sample
* semicolon-separated list of files with reads
* semicolon-separated list of files with mates reads

An example csv file (provided with the software as well - second testing scenario):

Sample name | List of fastq files (reads) | List of fastq files (mates)
-------------- | --------------- | ---------------
HG00331 | /tools/ERR018471_1.filt.fastq;/tools/ERR031898_1.filt.fastq | /tools/ERR018471_2.filt.fastq;/tools/ERR031898_2.filt.fastq

Bear in mind that the column headers are provided only for the ease of the example, and should not be present in the csv file.

## Running the pipeline

To get into the docker image for working with your data, it's best to mount local directories to the container:

```bash
docker run --mount type=bind,source=/mnt/,target=/mnt/ -p 8082:8082 -it mateuszchilinski/consensusv-pipeline:latest
```

In that example, we bind folder /mnt/, where working directory and samples will be stored to in-container folder /mnt/. Once in the container, we can run the pipeline using the following command:

```bash
python run_consensusv.py RunCSVFile --csv-file /mnt/data/samples.csv --workers 4 --working-dir /mnt/working_dir/
```
Remember to put your samples in the file samples.csv according to the [guidelines](#preparation-of-your-samples). In this case, we run the whole pipeline using 4 workers, that is maximum of 4 tasks will be run at once. 

Important notice: for the alignment and samtools operations (sorting, indexing etc.) we use 4 threads, the other SV callers and steps use mostly one. Bear that in mind when calculating how many workers you can run at once at your system (e.g. when you have computer with 18 cores, it might be a good idea to stick with 4 workers, as in the alignment phase all 16 cores will be utilised)! This behaviour (the number of threads) can be changed in the common.py file, however we do not recommend it, unless you are an advanced user and know what you are doing.

All the parameters that can be used with the script are shown in the following table:

Parameter | Description
-------------- | ---------------
--csv-file | File location of the csv file that described all the samples according to the [guidelines](#preparation-of-your-samples).
--working-dir | Working directory of the pipeline. It should have some free space left, as alignment steps can consume quite a lot of it.
--model | Optional parameter showing the pretrained model used by ConsensuSV. The model provided with the software is sufficient, and changing of it should be done if you know what you are doing (e.g. for changing the SV callers used in the pipeline).

## Output location

The location of the output depends on your working directory, provided as the parameter. In that directory, two folder will be created:
* output - a folder where ConsensuSV calls of Structural Variants are stored
* pipeline - where you will find folders for each of the sample, containing fully preprocessed .bam files, all VCF files from the individual SV calling tools, along with file with SNPs and Indels (separately, SNPs.vcf and Indels.vcf)

## Pipeline control webservice

The pipeline uses luigi framework for the execution of the tasks in specific order and parallelisation. That is why once can control the pipeline execution information using the webservice provided by luigi.

The webinterface is by default provided at:

```
http://localhost:8082/static/visualiser/index.html
```

For example, if we execute the testing scenario that trains the model from scratch, we can see the current phase of the pipeline, the previous ones and the next ones in form of an execution tree (click to enlarge):

<p align="center">
<img src="https://github.com/SFGLab/ConsensuSV-pipeline/blob/main/luigi_1000g_get.png" />
</p>

Of course one can also see the execution tree of CSV (in this example, 2 samples are being proceeded; click to enlarge):

<p align="center">
<img src="https://github.com/SFGLab/ConsensuSV-pipeline/blob/main/luigi_pipeline_2_samples.png" />
</p>

## Pipeline details

The overall schema of the pipeline is shown on the following picture:

<p align="center">
<img src="https://github.com/SFGLab/ConsensuSV-pipeline/blob/main/pipeline.png" />
</p>

First, the fastq files are merged - an option available for the experiments run e.g. in replicates or using multiple lanes. Secondly, QC analysis is performed (using FastQC) and the output of the analysis is available as one of the final files after the whole run. 

After the QC analysis, the 1000 Genomes best practices are used for the alignment and futher processing of the sample. First, the alignment is done using bwa-mem. Each of the alignment commends uses 4 cores for the alignment purposes. After that, the SAM file produced by bwa-mem is converted to BAM file using samtools - also using 4 threads. The alignment file is then sorted and indexed using samtools. After those steps, duplicates are marked and removed with usage of biobambam2 - a step followed by indexing the file once again.

Next steps use Genome Analysis ToolKit - the BaseRecalibrator and ApplyBQSR are used for the recalibration of the bases near known SNPs sites. Both steps are also derived from the 1000 Genomes guidelines. The final steps are sorting, indexing and cleaning up intermediate files, leaving the final sorted and indexed bam file.

After the final bam file is prepared, multiple tools are run in parallel to obtain the Structural Variants, Indels and SNPs. We are using bcftools for the Indels and SNPs callings. The SV-callers used in this pipeline are: Delly, BreakDancer, Tardis, CNVNator, BreakSeq, Manta, Lumpy, and Whamg.

The final step is merging the Structural Variant calls into one unified file using our ConsensuSV-core algorithm. For the details on it, please refer to ConsensuSV-core github repository (https://github.com/SFGLab/ConsensuSV-core).

## Setup on NVIDIA DGX A100 systems

The ConsensuSV-pipeline can be run using HPC software. The parallelism nature of luigi framework lets multiple samples to be processed at once. We have tested the pipeline on NVIDIA DGX A100 cluster, and the following requirements need to be met:
* slurm
* pyxis version at least 0.11.0
* enroot installed
* usage of --container-writable flag; most of the temp files are stored in the temporary direction provided by the user, however for testing scenarios & actual calculations some of the SV callers need to use space of the container - however, it is limited and there is no need for further adjustment

Preparation of the enroot image for DGX A100 systems can be done locally using the following commands:
```bash
enroot import docker://mateuszchilinski@mateuszchilinski/consensusv-pipeline
```

Bear in mind that because of the size of the container, you might be required to change the temporary folder for enroot before executing the previous command (:
```bash
export TMPDIR=/home/dir_to_your_temp_folder/
```

After having created enroot image, you need to upload it (mateuszchilinski+consensusv-pipeline.sqsh) to your DGX A100 system (using e.g. scp). After the upload is complete, you can run the container using the following command:

```bash
srun --pty --container-image ~/mateuszchilinski+consensusv-pipeline.sqsh --container-writable /bin/bash
```

Sometimes, before running this commend you need to set the environmental variable:

```bash
XDG_RUNTIME_DIR=~
```

However, since the sample should be out-of-the-container, it is recommended to mount the folder containing samples to the container (in the following example, we mount /dir/to/data location on the cluster to /data folder in the container). You can also mount more folders to the container, depending on what you want to do:

```bash
srun --pty --container-mounts /dir/to/data:/data:rw --container-image ~/mateuszchilinski+consensusv-pipeline.sqsh --container-writable /bin/bash
```

After running the container (which needs to be done using srun - limitation of the pysix), it is best to reconfigure the system depending on your HPC capibilities. Modify file:

```/etc/luigi/luigi.cfg```

e.g. using:

```bash
nano /etc/luigi/luigi.cfg
```

In the configuration file, you can edit the following lines (other ones are for advanced luigi users only and should be otherwise not modified):
```
io=16
cores=128
```
Where cores are the maximum cores that your server is capable of using (some of the scripts/programs in the pipeline use multiple cores, so it's a limit on total usage of CPU power on your HPC), and io is the maximum number of IO-heavy operations (e.g. sorting using samtools) that are allowed to run in parallel. If the pipeline has trouble with the central scheduler accessibility, it's probably because the IO operations are using all the power of your storage device, and the central scheduler becomes inaccesible. In that case, the best solution is to descrease allowed io-heavy operations by changing the config to smaller number.

After setting up the configuration you need to run central schelduler by yourself (again - entrypoints are not supported in pysix):

```bash
luigid --background
```

After that, you can start using the software, e.g. run:

```
./test_run_csv.sh
```

## Benchmark

We have used 9 samples for the benchmark provided by NYGC - HG00512, HG00513, HG00514, HG00731, HG00732, HG00733, NA19238, NA19239, NA19240. The comparisons were done using svbench (https://github.com/kcleal/svbench) and Venn diagrams of the common SVs. The results from svbench can be seen below:

<p align="center">
<img src="https://github.com/SFGLab/ConsensuSV-pipeline/blob/main/benchmark.png" />
</p>

And the Venn diagrams can be seen there:

<p align="center">
<img src="https://github.com/SFGLab/ConsensuSV-pipeline/blob/main/average.png" />
</p>

<p align="center">
<img src="https://github.com/SFGLab/ConsensuSV-pipeline/blob/main/venns.png" />
</p>

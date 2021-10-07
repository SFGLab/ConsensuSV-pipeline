# ConsensuSV-pipeline

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
docker run -it mateuszchilinski/consensusv-pipeline:latest /bin/bash
```

Then direct into the workspace containing all the pipeline data:

```shell
cd /workspace/
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

## Pipeline details

For the details on ConsensuSV algorithm for the consensus establishment, please refer to ConsensuSV-core (https://github.com/SFGLab/ConsensuSV-core).

## HPC-ready version for NVIDIA DGX A100 systems with SLURM

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
srun --container-image ~/mateuszchilinski+consensusv-pipeline.sqsh /bin/bash
```

However, since the sample should be out-of-the-container, it is recommended to mount the folder containing samples to the container (in the following example, we mount /dir/to/data location on the cluster to /data folder in the container). You can also mount more folders to the container, depending on what you want to do:

```bash
srun --container-mounts /dir/to/data:/data:rw --container-image ~/mateuszchilinski+consensusv-pipeline.sqsh /bin/bash
```

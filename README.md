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

Usage:

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


# syntax=docker/dockerfile:1

# INSTALLED: BreakDancer, CNVnator, delly, breakseq, lumpy, Manta (run on breakseq conda), tardis, svelter (run on breakseq conda), whamg, novoBreak

FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y upgrade && \
apt-get install -y wget tabix unzip && \
cd / && mkdir -p tools && \
mkdir -p test_working_dir && \
mkdir -p 1000g_train_working_dir

# static files

RUN cd /tools && \
wget ftp://ftp.ebi.ac.uk/1000g/ftp/technical/reference/GRCh38_reference_genome/other_mapping_resources/ALL_20141222.dbSNP142_human_GRCh38.snps.vcf.gz && \
tabix ALL_20141222.dbSNP142_human_GRCh38.snps.vcf.gz && \
wget ftp://ftp.ebi.ac.uk/1000g/ftp/technical/reference/GRCh38_reference_genome/GRCh38_full_analysis_set_plus_decoy_hla.* && \
wget ftp://ftp.ebi.ac.uk/1000g/ftp/phase3/data/HG00331/sequence_read/ERR018471_1.filt.fastq.gz && \
gunzip ERR018471_1.filt.fastq.gz && \
wget ftp://ftp.ebi.ac.uk/1000g/ftp/phase3/data/HG00331/sequence_read/ERR018471_2.filt.fastq.gz && \
gunzip ERR018471_2.filt.fastq.gz && \
wget ftp://ftp.ebi.ac.uk/1000g/ftp/phase3/data/HG00331/sequence_read/ERR031898_1.filt.fastq.gz && \
gunzip ERR031898_1.filt.fastq.gz && \
wget ftp://ftp.ebi.ac.uk/1000g/ftp/phase3/data/HG00331/sequence_read/ERR031898_2.filt.fastq.gz && \
gunzip ERR031898_2.filt.fastq.gz && \
wget https://github.com/BilkentCompGen/sonic-prebuilt/raw/master/GRCh38_1kg.sonic && \
wget http://sv.gersteinlab.org/phase1bkpts/breakseq2_bplib_20150129.zip && \
unzip breakseq2_bplib_20150129.zip && \
cat breakseq2_bplib_20150129.gff | awk -v OFS='\t' '$1="chr"$1' > breakseq2_bplib_20150129_chr.gff && \
sed -E 's/[0-9,X,Y].*/chr&/' breakseq2_bplib_20150129.ins > breakseq2_bplib_20150129_chr.ins && \
sed -E 's/[0-9,X,Y].*/chr&/' breakseq2_bplib_20150129.fna > breakseq2_bplib_20150129_chr.fna && \
rm breakseq2_bplib_20150129.*

# updates / packages
ENV LANGUAGE=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# long downloads are up, worth updating again
RUN apt-get update 

RUN apt-get install -y build-essential gfortran xorg-dev libpcre3-dev \
        libncurses5-dev zlib1g-dev libbz2-dev liblzma-dev libcurl3-dev git fort77 libreadline-dev \
        cmake curl libboost-all-dev libgd-dev default-jre nano libncurses5 bc locales bsdmainutils gawk && \
        locale-gen en_US.UTF-8

# necessary toolkits

# anaconda

RUN cd /tools && \
wget https://repo.anaconda.com/archive/Anaconda3-2021.05-Linux-x86_64.sh && \
bash Anaconda3-2021.05-Linux-x86_64.sh -b -p /tools/anaconda && \
rm Anaconda3-2021.05-Linux-x86_64.sh

SHELL ["/bin/bash", "-c"]

# htslib

RUN cd /tools && \
    wget https://github.com/samtools/htslib/releases/download/1.12/htslib-1.12.tar.bz2 && \
    tar xjf htslib-1.12.tar.bz2 && \
    rm htslib-1.12.tar.bz2 && \
    cd htslib-1.12 && \
    ./configure --prefix $(pwd) && \
    make
# samtools

RUN cd /tools && \
    wget https://github.com/samtools/samtools/releases/download/1.12/samtools-1.12.tar.bz2 && \
    tar xjf samtools-1.12.tar.bz2 && \
    rm samtools-1.12.tar.bz2 && \
    cd samtools-1.12 && \
    ./configure --prefix $(pwd) && \
    make

RUN cd /tools && \
    wget https://jztkft.dl.sourceforge.net/project/samtools/samtools/0.1.19/samtools-0.1.19.tar.bz2 && \
    tar xjf samtools-0.1.19.tar.bz2 && \
    rm samtools-0.1.19.tar.bz2 && \
    cd samtools-0.1.19 && \
    make

# bcftools

RUN cd /tools && \
    wget https://github.com/samtools/bcftools/releases/download/1.12/bcftools-1.12.tar.bz2 && \
    tar xjf bcftools-1.12.tar.bz2 && \
    rm bcftools-1.12.tar.bz2 && \
    cd bcftools-1.12 && \
    ./configure --prefix $(pwd) && \
    make

# bwa

RUN cd /tools && \ 
wget https://netcologne.dl.sourceforge.net/project/bio-bwa/bwa-0.7.17.tar.bz2 && \ 
tar xjf bwa-0.7.17.tar.bz2 && \ 
rm bwa-0.7.17.tar.bz2 && \
cd bwa-0.7.17 && \ 
make

# bwakit

RUN cd /tools && \
wget https://netcologne.dl.sourceforge.net/project/bio-bwa/bwakit/bwakit-0.7.15_x64-linux.tar.bz2 && \ 
tar xjf bwakit-0.7.15_x64-linux.tar.bz2 && \ 
rm bwakit-0.7.15_x64-linux.tar.bz2 && \
cp bwa.kit/resource-GRCh38/hs38DH.fa.alt .

# biobambam2

RUN cd /tools && \ 
wget https://github.com/gt1/biobambam2/releases/download/2.0.87-release-20180301132713/biobambam2-2.0.87-release-20180301132713-x86_64-etch-linux-gnu.tar.gz && \
tar -xzf biobambam2-2.0.87-release-20180301132713-x86_64-etch-linux-gnu.tar.gz && \
rm biobambam2-2.0.87-release-20180301132713-x86_64-etch-linux-gnu.tar.gz

# bcftools

RUN cd /tools && \
wget https://github.com/samtools/bcftools/releases/download/1.11/bcftools-1.11.tar.bz2 && \
tar xjf bcftools-1.11.tar.bz2 && \
rm bcftools-1.11.tar.bz2

# root

RUN cd /tools && \
mkdir root && \
wget https://root.cern/download/root_v6.24.00.Linux-ubuntu20-x86_64-gcc9.3.tar.gz && \ 
tar -xzf root_v6.24.00.Linux-ubuntu20-x86_64-gcc9.3.tar.gz && \ 
rm root_v6.24.00.Linux-ubuntu20-x86_64-gcc9.3.tar.gz && \
source /tools/root/bin/thisroot.sh

ENV ROOTSYS=/tools/root
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ROOTSYS/lib

RUN ((echo y;echo o conf prerequisites_policy follow;echo o conf commit)|cpan) && \
cpan GD && \
cpan GD::Graph && \
cpan Statistics::Descriptive && \
cpan GD::Graph::histogram

# GATK

RUN cd tools && \
wget https://github.com/broadinstitute/gatk/releases/download/4.2.0.0/gatk-4.2.0.0.zip && \
unzip gatk-4.2.0.0.zip && \
rm gatk-4.2.0.0.zip

# FastQC

RUN cd tools && \
wget https://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.11.9.zip && \
unzip fastqc_v0.11.9.zip && \
rm fastqc_v0.11.9.zip && \
chmod +x FastQC/fastqc

# vcftools

RUN cd tools && \
wget https://downloads.sourceforge.net/project/vcftools/vcftools_0.1.13.tar.gz && \
tar -xzf vcftools_0.1.13.tar.gz && \ 
rm vcftools_0.1.13.tar.gz

ENV PATH=${PATH}:/tools/samtools-1.12:/tools/bcftools-1.12:/tools/bwa-0.7.17:/tools/anaconda/bin:/tools/biobambam2/2.0.87-release-20180301132713/x86_64-etch-linux-gnu/bin:/tools/gatk-4.2.0.0:/tools/FastQC:/tools/vcftools_0.1.13/cpp:/tools/bedtools2/bin

RUN conda init bash

# bedtools2

RUN cd tools && \
wget https://github.com/arq5x/bedtools2/releases/download/v2.30.0/bedtools-2.30.0.tar.gz && \
tar -xzf bedtools-2.30.0.tar.gz && \ 
rm bedtools-2.30.0.tar.gz && \
cd bedtools2 && \
make

# SV callers

# CNVNator

RUN cd /tools && \
wget https://github.com/abyzovlab/CNVnator/archive/refs/heads/master.zip && \
unzip master.zip && \
rm master.zip && \
cd CNVnator-master/ && \
ln -s /tools/samtools-1.12 samtools && \
make 

# breakdancer

RUN cd /tools && \
wget https://github.com/genome/breakdancer/archive/refs/heads/master.zip && \
unzip master && \
rm master.zip && \
cd breakdancer-master/ && \
cmake . && \
make -Wnoparentheses -Wnounused-local-typedefs -Wnodeprecated-declarations && \
cd /tools/breakdancer-master/bin && \
wget https://raw.githubusercontent.com/PapenfussLab/sv_benchmark/master/breakdancer2vcf.py

# delly

RUN cd /tools && \
wget https://github.com/dellytools/delly/releases/download/v0.8.7/delly_v0.8.7_linux_x86_64bit && \
chmod a+x delly_v0.8.7_linux_x86_64bit

# breakseq

RUN conda create --name breakseq python=2.7 numpy && \
conda run -n breakseq pip install https://github.com/bioinform/breakseq2/archive/2.2.tar.gz

# lumpy

RUN apt-get install libssl-dev && \
cd /tools/ && \
git clone --recursive https://github.com/arq5x/lumpy-sv.git && \
cd lumpy-sv && \
conda run -n breakseq make

# manta

RUN cd /tools/ && \
wget https://github.com/Illumina/manta/releases/download/v1.6.0/manta-1.6.0.centos6_x86_64.tar.bz2 && \
tar xjf manta-1.6.0.centos6_x86_64.tar.bz2 && \
rm manta-1.6.0.centos6_x86_64.tar.bz2

# tardis

RUN cd /tools/ && \
git clone https://github.com/BilkentCompGen/tardis.git --recursive && \
cd tardis && \
make libs && \
make

# svelter

RUN cd /tools/ && \
git clone https://github.com/mills-lab/svelter.git && \
cd svelter && \
conda run -n breakseq python setup.py install && \
sed -i-e '351,353d;849,851d;1825,1828d;1946,1949d;6381,6384d;10935,10938d' svelter_sv/svelter.py && \
sed -i "s/if not chrom_single in chromos:/chromos=chrom_single.split(',')/g" svelter_sv/svelter.py
# wham

RUN cd /tools/ && \
git clone --recursive  https://github.com/zeeev/wham.git && \
cd wham/src/bamtools/ && \
mkdir lib && \
git checkout master && \
cmake -DCMAKE_INSTALL_PREFIX=. && \
make && \
cp src/libbamtools.a lib/ && \
cd /tools/wham && \
make

# novoBreak

RUN cd /tools/ && \
git clone https://github.com/czc/nb_distribution.git

# ConsensuSV

RUN cd /tools && \
    wget https://github.com/SFGLab/ConsensuSV-core/archive/refs/tags/1.7.zip && \
    unzip 1.7.zip && \
    rm 1.7.zip && \
    mv ConsensuSV-core-1.7 ConsensuSV-core && \
    cd ConsensuSV-core && \
    unzip ALL_Illumina_Integrate_20170206.zip

ENV PATH=$PATH:/tools/lumpy-sv/bin:/tools/manta-1.6.0.centos6_x86_64/bin:/tools/tardis:/tools/wham/bin:/tools/breakdancer-master/bin:/tools/breakdancer-master/perl:/tools/nb_distribution/:/tools/CNVnator-master:/tools:/tools/ConsensuSV

RUN pip install pysam wget luigi

RUN mkdir /etc/luigi/ && \ 
touch luigi.cfg && \
printf "[core]\n\
log_level=ERROR\n\
rpc_connect_timeout=60\n\
rpc_retry_wait=120\n\
rpc_retry_attempts=100\n\
[resources]\n\
io=16\n\
cores=128\n\
[worker]\n\
keep_alive=true\n\
[scheduler]\n\
worker_disconnect_delay=7200" > /etc/luigi/luigi.cfg

WORKDIR /workspace

RUN cd /workspace/ && \
git clone https://github.com/SFGLab/ConsensuSV-pipeline.git .

EXPOSE 8082

ENTRYPOINT luigid --background & /bin/bash

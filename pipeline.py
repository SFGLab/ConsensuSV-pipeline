bwa index GRCh38_full_analysis_set_plus_decoy_hla.fa
samtools faidx GRCh38_full_analysis_set_plus_decoy_hla.fa
bwa mem -t 1 -B 4 -O 6 -E 1 -M -R "@RG\tID:SRR\tLB:LIB_1\tSM:SAMPLE_1\tPL:ILLUMINA" GRCh38_full_analysis_set_plus_decoy_hla.fa SRR590764_1.filt.fastq SRR590764_2.filt.fastq > SRR.sam
samtools view -S -b SRR.sam > SRR.bam
samtools sort SRR.bam > SRR_sorted.bam
samtools index SRR_sorted.bam

bammarkduplicates I=SRR_sorted.bam O=SRR_sorted_p2.bam index=1 rmdup=1

gatk BaseRecalibrator -R /tools/GRCh38_full_analysis_set_plus_decoy_hla.fa -O SRR_sorted_recal_data.table -I SRR_sorted.bam -known-sites /tools/ALL_20141222.dbSNP142_human_GRCh38.ss.vcf.gz
gatk ApplyBQSR -R /tools/GRCh38_full_analysis_set_plus_decoy_hla.fa -O SRR_sorted_final.bam -I SRR_sorted.bam -bqsr-recal-file SRR_sorted_recal_data.table


samtools-1.11/samtools sort SRR_final.bam > SRR_final_sorted.bam
samtools-1.11/samtoolsindex SRR_final_sorted.bam


breakdancer-1.4.5/perl/bam2cfg.pl SRR_final_sorted.bam > breakdancer.cfg
breakdancer-1.4.5/bin/breakdancer-max breakdancer.cfg > breakdancer.calls
python breakdancer2vcf.py <breakdancer.calls > breakdancer.vcf

./delly_v0.8.7_linux_x86_64bit call -o delly.bcf -g GRCh38_full_analysis_set_plus_decoy_hla.fa SRR_final_sorted.bambcftools view delly.bcf > delly.vcf

bcftools mpileup -Ou -f GRCh38_full_analysis_set_plus_decoy_hla.fa SRR_final_sorted.bam | bcftools call -mv -Ob -o SRR_SNPs.bcfbcftools view -i '%QUAL>=20' SRR_SNPs.bcf > SRR_SNPs.vcf
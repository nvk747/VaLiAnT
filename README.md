# VaLiAnT

The Variant Library Annotation Tool (VaLiAnT) is an oligonucleotide library design and annotation tool for Saturation Genome Editing and other Deep Mutational Scanning experiments.

Two BRCA1 libraries are included in the `examples` directory, including all necessary inputs and [instructions](examples/README.md) to generate them.

Please also see the [VaLiAnT Wiki](https://github.com/cancerit/VaLiAnT/wiki) for more information on use cases.

* [Usage](#usage)
  * [Python package](#python-package)
  * [Docker image](#docker-image)
  * [Singularity image](#singularity-image)
* [Command line interface](#command-line-interface)
* [Mutation types](#mutation-types)
  * [Single-nucleotide deletion](#single-nucleotide-deletion)
  * [Two-nucleotide deletion](#two-nucleotide-deletion)
  * [Single-nucleotide variant](#single-nucleotide-variant)
  * [In-frame deletion](#in-frame-deletion)
  * [Alanine codon substitution](#alanine-codon-substitution)
  * [Stop codon substitution](#stop-codon-substitution)
  * [All amino acid codon substitution](#all-amino-acid-codon-substitution)
  * [SNVRE](#snvre)
  * [Custom variants](#custom-variants)
* [Installation](#installation)
  * [Python virtual environment](#python-virtual-environment)
  * [Docker image](#docker-image-1)
* [File formats](#file-formats)
  * [Targeton file](#targeton-file)
  * [VCF manifest file](#vcf-manifest-file)
  * [PAM protection VCF file](#pam-protection-vcf-file)
  * [Oligonucleotide metadata file](#oligonucleotide-metadata-file)
  * [Variant file](#variant-file)
  * [Unique oligonucleotides file](#unique-oligonucleotides-file)
  * [Reference sequence retrieval quality check file](#reference-sequence-retrieval-quality-check-file)
* [Development](#development)
* [LICENSE](#license)

## Usage

See the [command line interface](#command-line-interface) section for the full list and a more detailed description of the parameters.

Input parameters:

- species
- assembly
- 5' adaptor (optional)
- 3' adaptor (optional)

Input files:

- [targeton file](#targeton-file) (TSV)
- reference genome sequence (FASTA)
- reference genome index (FAI)
- [PAM protection file](#pam-protection-vcf-file) (VCF, optional)
- [VCF manifest file](#vcf-manifest-file) (CSV, optional)
- custom variant files (VCF, optional)
- features file (GTF/GFF2, optional)
- codon table with frequencies (CSV, optional)

Output files:

- [reference sequence retrieval quality check file](#reference-sequence-retrieval-quality-check-file) (CSV)
- [oligonucleotide metadata file](#oligonucleotide-metadata-file) (CSV)
- [variant file](#variant-file) (VCF)
- [unique oligonucleotides file](#unique-oligonucleotides-file) (CSV)

The reference directory should contain both the FASTA file and its index; *e.g.*, if the FASTA file is named `genome.fa`, a `genome.fa.fai` file should also be present in the same directory. When running the tool in a container, the directory containing both files should therefore be mounted.

The features file (`gff` option) is required to detect exonic regions in the targeton, and should therefore be provided in most circumstances. The files should only contain features for one transcript per gene (the `gene_id` and `transcript_id` attributes are required to perform this check). The features file should match the assembly of the target reference genome. Any features of type other than `CDS` and `UTR` are ignored.

If the `codon-table` option is not set, [this table](src/valiant/data/default_codon_table.csv) will be used.

Ambiguous nucleotides are not allowed in the reference sequence. Soft-masking is ignored.

Oligonucleotides exceeding a given length (`max-length` option) will not be included in the unique oligonucleotide files and their metadata will be stored in separate files marked as 'excluded'.

### Python package

After [installing](#python-virtual-environment) the package in an appropriate virtual environment:

```sh
valiant \
    ${TARGETONS_FILE} \
    ${REFERENCE_FILE} \
    ${OUTPUT_DIR} \
    ${SPECIES} \
    ${ASSEMBLY} \
    --gff ${GTF_FILE} \
    --adaptor-5 ${ADAPTOR_5} \
    --adaptor-3 ${ADAPTOR_3}
```

### Docker image

After [building](#docker-image-1) or pulling the Docker image (`quay.io/wtsicgp/valiant:X.X.X`, where `X.X.X` is a version tag):

```sh
docker run \
    -v ${HOST_INPUTS}:${INPUT_DIR}:ro \
    -v ${HOST_REF}:${REF_DIR}:ro \
    -v ${HOST_OUTPUT}:${OUTPUT_DIR} \
    valiant \
        valiant \
            ${INPUT_DIR}/${TARGETONS_FILE} \
            ${REF_DIR}/${REFERENCE_FILE} \
            ${OUTPUT_DIR} \
            ${SPECIES} \
            ${ASSEMBLY} \
            --gff ${INPUT_DIR}/${GTF_FILE} \
            --adaptor-5 ${ADAPTOR_5} \
            --adaptor-3 ${ADAPTOR_3}
```

The `HOST_*` environment variables represent local paths to be mounted by the Docker container.

### Singularity image

After pulling the Docker image with Singularity:

```sh
singularity exec \
    --cleanenv \
    -B ${HOST_INPUTS}:${INPUT_DIR}:ro \
    -B ${HOST_REF}:${REF_DIR}:ro \
    -B ${HOST_OUTPUT}:${OUTPUT_DIR} \
    ${SINGULARITY_IMAGE} \
        valiant \
            ${INPUT_DIR}/${TARGETONS_FILE} \
            ${REF_DIR}/${REFERENCE_FILE} \
            ${OUTPUT_DIR} \
            ${SPECIES} \
            ${ASSEMBLY} \
            --gff ${INPUT_DIR}/${GTF_FILE} \
            --adaptor-5 ${ADAPTOR_5} \
            --adaptor-3 ${ADAPTOR_3}
```

## Command line interface

|Argument|Format|Description|
|-|-|-|
|`OLIGO_INFO`|file path|Path to the [targeton file](#targeton-file).|
|`REF_FASTA`|file path|Path to the FASTA file of the target reference genome.|
|`OUTPUT`|file path|Output path (should exist already).|
|`SPECIES`|species name|Target species, to be reported in the oligonucleotide metadata.|
|`ASSEMBLY`|assembly name|Target assembly, to be reported in the oligonucleotide metadata.|

|Option|Format|Default|Description|
|-|-|-|-|
|`codon-table`|file path|-|Path to a codon table with frequencies.|
|`gff`|file path|-|Path to GTF/GFF2 file containing CDS and UTR features; one transcript per gene only.|
|`pam`|file path|-|Path to a [PAM protection file](#pam-protection-vcf-file).|
|`vcf`|file path|-|Path to a [VCF manifest file](#vcf-manifest-file).|
|`adaptor-5`|DNA sequence|-|DNA sequence to be added at the 5' end of the oligonucleotide.|
|`adaptor-3`|DNA sequence|-|DNA sequence to be added at the 3' end of the oligonucleotide.|
|`revcomp-minus-strand`|flag|`false`|For minus strand targets, include the reverse complement of the mutated reference sequence in the oligonucleotide.|
|`version`|flag|`false`|Show the version of the tool and quit.|
|`sequences-only`|flag|`false`|Generate the [reference sequence retrieval quality check file](#reference-sequence-retrieval-quality-check-file) and quit.
|`max-length`|integer|300|Maximum oligonucleotide length.|
|`log`|log level|`WARNING`|Name of the preferred log level (see the [official documentation](https://docs.python.org/3.7/library/logging.html#levels) of the `logging` module).|

## Mutation types

Types of mutation that apply to any target (label):

- [single-nucleotide deletion](#single-nucleotide-deletion) (`1del`)
- [two-nucleotide deletion](#two-nucleotide-deletion) (`2del0`, `2del1`)
- [single-nucleotide variant](#single-nucleotide-variant) (`snv`)

Types of mutation that apply to CDS targets only (label):

- [in-frame deletion](#in-frame-deletion) (`inframe`)
- [alanine codon substitution](#alanine-codon-substitution) (`ala`)
- [stop codon substitution](#stop-codon-substitution) (`stop`)
- [all amino acid codon substitution](#all-amino-acid-codon-substitution) (`aa`)
- [SNVRE](#snvre) (`snvre`)

[Variants imported from VCF files](#custom-variants) are labelled as `custom`.

### Single-nucleotide deletion

A single nucleotide is deleted at any one position of the target.

Given the target `ACGT`, *e.g.*:

```
CGT
AGT
ACT
ACG
```

### Two-nucleotide deletion

Non-overlapping pairs of nucleotides are deleted starting from the first (`2del0`) or the second (`2del1`) nucleotide. No partial (single-nucleotide) deletions are performed at the end of sequences with an odd or even length when the start offset is zero or one, respectively.

Given the target `ACGTAAA` and start offset zero (`2del0`), *e.g.*:

```
GTAAA
ACAAA
ACGTA
```

With start offset one (`2del1`), *e.g.*:

```
ATAAA
ACGAA
ACGTA
```

### Single-nucleotide variant

Each nucleotide is replaced with all the alternatives.

Given the target `AA`, *e.g.*:

```
CA
GA
TA
AC
AG
AT
```

For CDS targets, the resulting amino acid change is reported.

### In-frame deletion

Only for CDS targets.

Delete each triplet so that the reading frame is preserved.

Given the target `GAAATTTGG` with frame 2, *e.g.*:

```
GTTTGG
GAAAGG
```

### Alanine codon substitution

Only for CDS targets.

Replace each codon with the top-ranking alanine codon.

Given the target `GCAAAATTT`, with `GCC` being the top-ranking alanine codon, *e.g.*:

```
GCCAAATTT
GCAGCCTTT
GCAAAAGCC
```

### Stop codon substitution

Only for CDS targets.

Replace each codon with the top-ranking stop codon.

Given the target `TAACCCGGG`, with `TGA` being the top-ranking stop codon, *e.g.*:

```
TGACCCGGG
TAATGAGGG
TAACCCTGA
```

### All amino acid codon substitution

Only for CDS targets.

Replace each codon with the top-ranking codon of all amino acids. Given the default codon table, this results in 19 mutated sequences for each codon mapping to an amino acid (the reference amino acid being excluded) and 20 for each stop codon.

Given the target `AAATGA` on the plus strand, *e.g.* (each column representing the sequences generated from one codon):

```
ATCTGA  AAAATC
ATGTGA  AAAATG
ACCTGA  AAAACC
AACTGA  AAAAAC
        AAAAAG
AGCTGA  AAAAGC
CGGTGA  AAACGG
CTGTGA  AAACTG
CCCTGA  AAACCC
CACTGA  AAACAC
CAGTGA  AAACAG
GTGTGA  AAAGTG
GCCTGA  AAAGCC
GACTGA  AAAGAC
GAGTGA  AAAGAG
GGCTGA  AAAGGC
TTCTGA  AAATTC
TACTGA  AAATAC
TGCTGA  AAATGC
TGGTGA  AAATGG
```

### SNVRE

Only for CDS targets.

Given a set of [SNV](#single-nucleotide-variant)'s, replace triplets according to the following rules:

- if the SNV results in a synonymous mutation, replace the triplet with all the synonymous triplets of the variant
- if the SNV results in a missense mutation, replace the triplet with the top-ranking synonymous triplet of the variant
- if the SNV results in a nonsense mutation, replace the triplet with the top-ranking stop codon

For a given missense or nonsense SNV mutation, if the resulting triplet is already the top-ranking one, the second highest ranking triplet is used to generate the SNVRE mutation instead.

Given the following SNV's for sequence `AAAAGT`, *e.g.*:

```
mseq	ref	alt
CAAAGT	K	Q
GAAAGT	K	E
TAAAGT	K	STOP
ACAAGT	K	T
AGAAGT	K	R
ATAAGT	K	I
AACAGT	K	N
AAGAGT	K	K
AATAGT	K	N
...
AAAAGC	S	S
...
```

There is only one synonymous mutation for the first triplet (`AAGAGT`), but since lysine maps to only two codons and one of them is the reference, no SNVRE variants are generated from it. The one for the second triplet (`AAAAGC`), though, results in the top-ranking codon for serine, that maps to six codons, and therefore the following four SNVRE's are generated:

```
mseq	ref	alt
AAATCA	S	S
AAATCC	S	S
AAATCG	S	S
AAATCT	S	S
```

For missense mutations, the top-ranking codon (the current being excluded) for each alternative amino acid replaces the reference sequence:

```
mseq	ref	alt	snv	svnre
CAAAGT	K	Q	CAA	CAG
GAAAGT	K	E	GAA	GAG
ACAAGT	K	T	ACA	ACC
AGAAGT	K	R	AGA	CGG
ATAAGT	K	I	ATA	ATC
AACAGT	K	N	AAC	AAT
AATAGT	K	N	AAT	AAC
```

The resulting SNVRE variants would be:

```
mseq	ref	alt
CAGAGT	K	Q
GAGAGT	K	E
ACCAGT	K	T
CGGAGT	K	R
ATCAGT	K	I
AATAGT	K	N
AACAGT	K	N
```

For the nonsense mutation:

```
mseq	ref	alt	snv	svnre
TAAAGT	K	STOP	TAA	TGA
```

The resulting SNVRE variant would be:

```
mseq	ref	alt
TGAAGT	K	STOP
```

Unique codons do not generate SNVRE variants.

### Custom variants

Applied to the targeton reference sequence as a whole. Only simple variants such as the following are supported:

- substitutions
- insertions (*see below*)
- deletions (*see below*)
- indels

The classification of the variants is based exclusively on the `POS`, `REF`, and `ALT` fields to be agnostic with respect to the VCF source.

While in the VCF format insertion and deletion positions refer to the base preceding the event and the reference and alternative sequences both include the preceding (or following, if the variants start at position one) base, for consistency with the conventions adopted for generated mutations, in the [metadata table](#oligonucleotide-metadata-file) such variants are reported as shifted right by one and omitting the preceding (or following) base in the reference and alternative sequences.

## Installation

### Python virtual environment

Requirements:

- Python 3.7+

To install in a virtual environment:

```sh
# Initialise the virtual environment
python3.7 -m venv .env

# Activate the virtual environment
source .env/bin/activate

# Install the dependencies
pip install cython
pip install -r src/requirements.txt

# Install the valiant package
pip install src/
```

### Docker image

To build the Docker container:

```sh
docker build -t valiant .
```

## File formats

### Targeton file

Tab-separated values (TSV) file describing the reference sequence coordinates and the [types of mutation](#mutation-types) to be applied to the three target regions therein contained (collectively referred to as *targeton*). Multiple types of mutations can be applied to each target region. The coordinates of the target regions are derived from the genomic range of the second target region and an extension vector describing the lengths of the preceding and following regions.

Duplicate mutation types in any given group within the action vector are ignored.

Spacing is ignored when parsing the extension and action vectors.

The chromosome name needs to match the naming in the GTF/GFF2 file and in the reference genome.

|Field|Format|Description|
|-|-|-|
|`sgrna_id`|string|sgRNA identifier.|
|`ref_chr`|string|Chromosome name.|
|`ref_strand`|`+` or `-`|DNA strand.|
|`ref_start`|integer|Start position of the reference sequence.|
|`ref_end`|integer|End position of the reference sequence.|
|`r2_start`|integer|Start position of the second target region.|
|`r2_end`|integer|End position of the second target region.|
|`ext_vector`|`<int>, <int>`|Lengths of the first and third target regions.|
|`action_vector`|`(<str>, ...), (<str>, ...), (<str>, ...)`|[Type of mutation](#mutation-types) labels grouped by target region.|
|`sgrna_vector`|`<str>, ...`|sgRNA identifiers matching with `SGRNA` tags in the [PAM protection VCF file](#pam-protection-vcf-file).|

Example:

```
ref_chr	ref_strand	ref_start	ref_end	r2_start	r2_end	ext_vector	action_vector	sgrna_vector
chrX	+	41334132	41334320	41334253	41334297	25, 15	(1del), (1del, snv), (1del)	sgrna_1, sgrna_2
```

### VCF manifest file

CSV file listing the VCF files from which to import variants. Each VCF file is given an alias. If a tag is specified (`vcf_id_tag`), the VCF `INFO` field will be expected to contain it and its values will be used as variant identifiers; if no tag is specified, the `ID` field will be used instead.

|Field|Format|Description|
|-|-|-|
|`vcf_alias`|string|VCF file alias.|
|`vcf_id_tag`|VCF tag|(Optional) Variant ID tag.|
|`vcf_path`|file path|VCF file path.|

Example:

```
vcf_alias,vcf_id_tag,vcf_path
clinvar_1,ALLELEID,clinvar_abc.vcf
clinvar_2,ALLELEID,clinvar_xyz.vcf
gnomad,,gnomad_abc.vcf
```

### PAM protection VCF file

VCF file containing single-nucleotide substitution variants linked to sgRNA identifiers via the `SGRNA` tag.

Example:

```
##fileformat=VCFv4.3
##INFO=<ID=SGRNA,Number=1,Type=String,Description="sgRNA identifier">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chrX	41334252	.	G	C	.	.	SGRNA=sgRNA_1
chrX	41337416	.	C	T	.	.	SGRNA=sgRNA_2
chrX	41339064	.	G	A	.	.	SGRNA=sgRNA_3
chrX	41341504	.	T	C	.	.	SGRNA=sgRNA_4
chrX	41341509	.	G	A	.	.	SGRNA=sgRNA_4
```

### Oligonucleotide metadata file

Comma-separated values (CSV) file containing name, label, and all metadata of the oligonucleotides generated for any given targeton.

|Field|Format|Description|
|-|-|-|
|`oligo_name`|string|Name of the oligonucleotide.|
|`species`|species name|Species.|
|`assembly`|assembly name|Assembly.|
|`gene_id`|string|Gene ID.|
|`transcript_id`|string|Transcript ID.|
|`ref_chr`|string|Chromosome name.|
|`ref_strand`|`+`\|`-`|DNA strand.|
|`ref_start`|integer|Start position of the reference sequence.|
|`ref_end`|integer|End position of the reference sequence.|
|`revc`|0\|1|Whether the oligonucleotide contains the reverse complement of the reference sequence (minus strand transcripts only).|
|`ref_seq`|DNA sequence|Reference sequence.|
|`pam_seq`|DNA sequence|PAM-protected reference sequence.|
|`vcf_alias`|string|VCF file alias (custom mutations only).|
|`vcf_var_id`|string|Variant ID (custom mutations only).|
|`mut_position`|integer|Start position of the mutation.|
|`ref`|DNA sequence|Reference nucleotide or triplet.|
|`new`|DNA sequence|Mutated nucleotide or triplet. Not set for deletions.|
|`ref_aa`|amino acid|Reference amino acid.|
|`alt_aa`|amino acid|Alternative amino acid.|
|`mut_type`|`syn`\|`mis`\|`non`|Mutation type.|
|`mutator`|type of mutator|Label of the [type of mutator](#mutation-types) that generated the oligonucleotide.|
|`oligo_length`|integer|Oligonucleotide length.|
|`mseq`|DNA sequence|Full oligonucleotide sequence (with adaptors, if any).|

Example:

```
oligo_name,species,assembly,gene_id,transcript_id,ref_chr,ref_strand,ref_start,ref_end,revc,ref_seq,pam_seq,vcf_alias,vcf_var_id,mut_position,ref,new,ref_aa,alt_aa,mut_type,mutator,mseq
ENST00000460680.6.ENSG00000163930.10_chr3:52401117_C>T_snv_rc,homo sapiens,GRCh38,ENSG00000163930.10,ENST00000460680.6,chr3,-,52401056,52401300,1,TTTACAGGGGCTAGAGGGGTCAAGCTGTGCTCAGCCCAGAGGCAGCTGCCACACTTGCCAGCACCCCCCACTCAGTCACTATGTACAGATAAAGGGGCCTGCTTGGATCACCTTTTTCAAAGCCATCTGGCAGAGGCCATGGGGCTGTGTTGGGGCCTGGGCTCCAGAGGCACTGCTGGGCCCATTACCCCTTGGCATCAGGTCCTCTGGAACACAGGGGCTCCAACGGGTTGTCTTGATCCTGC,TTTACAGGGGCTAGAGGGGTCAAGCTGTGCTCAGCCCAGAGGCAGCTGCCACACTTGCCAGCACCCCCCACTCAGTCACTATGTACAGATAAAGGGGCCTGCTTGGATCACCTTTTTCAAAGCCATCTGGCAGAGGCCATGGGGCTGTGTTGAAACCTGGGCTCCAGAGGCACTGCTGGGCCCATTACCCCTTGGCATCAGGTCCTCTGGAACACAGGGGCTCCAACGGGTTGTCTTGATCCTGC,,,52401117,C,T,,,,snv,AATGATACGGCGACCACCGAGCAGGATCAAGACAACCCGTTGGAGCCCCTGTGTTCCAGAGGACCTGATGCCAAGGGGTAATGGGCCCAGCAGTGCCTCTGGAGCCCAGGTTTCAACACAGCCCCATGGCCTCTGCCAGATGGCTTTGAAAAAGGTGATCCAAGCAGGCCCCTTTATCTGTACATAGTGACTGAGTGGGGGGTACTGGCAAGTGTGGCAGCTGCCTCTGGGCTGAGCACAGCTTGACCCCTCTAGCCCCTGTAAATCGTATGCCGTCTTCTGCTTG
ENST00000460680.6.ENSG00000163930.10_chr3:52401117_C>G_snv_rc,homo sapiens,GRCh38,ENSG00000163930.10,ENST00000460680.6,chr3,-,52401056,52401300,1,TTTACAGGGGCTAGAGGGGTCAAGCTGTGCTCAGCCCAGAGGCAGCTGCCACACTTGCCAGCACCCCCCACTCAGTCACTATGTACAGATAAAGGGGCCTGCTTGGATCACCTTTTTCAAAGCCATCTGGCAGAGGCCATGGGGCTGTGTTGGGGCCTGGGCTCCAGAGGCACTGCTGGGCCCATTACCCCTTGGCATCAGGTCCTCTGGAACACAGGGGCTCCAACGGGTTGTCTTGATCCTGC,TTTACAGGGGCTAGAGGGGTCAAGCTGTGCTCAGCCCAGAGGCAGCTGCCACACTTGCCAGCACCCCCCACTCAGTCACTATGTACAGATAAAGGGGCCTGCTTGGATCACCTTTTTCAAAGCCATCTGGCAGAGGCCATGGGGCTGTGTTGAAACCTGGGCTCCAGAGGCACTGCTGGGCCCATTACCCCTTGGCATCAGGTCCTCTGGAACACAGGGGCTCCAACGGGTTGTCTTGATCCTGC,,,52401117,C,G,,,,snv,AATGATACGGCGACCACCGAGCAGGATCAAGACAACCCGTTGGAGCCCCTGTGTTCCAGAGGACCTGATGCCAAGGGGTAATGGGCCCAGCAGTGCCTCTGGAGCCCAGGTTTCAACACAGCCCCATGGCCTCTGCCAGATGGCTTTGAAAAAGGTGATCCAAGCAGGCCCCTTTATCTGTACATAGTGACTGAGTGGGGGGTCCTGGCAAGTGTGGCAGCTGCCTCTGGGCTGAGCACAGCTTGACCCCTCTAGCCCCTGTAAATCGTATGCCGTCTTCTGCTTG
ENST00000460680.6.ENSG00000163930.10_chr3:52401117_1del_rc,homo sapiens,GRCh38,ENSG00000163930.10,ENST00000460680.6,chr3,-,52401056,52401300,1,TTTACAGGGGCTAGAGGGGTCAAGCTGTGCTCAGCCCAGAGGCAGCTGCCACACTTGCCAGCACCCCCCACTCAGTCACTATGTACAGATAAAGGGGCCTGCTTGGATCACCTTTTTCAAAGCCATCTGGCAGAGGCCATGGGGCTGTGTTGGGGCCTGGGCTCCAGAGGCACTGCTGGGCCCATTACCCCTTGGCATCAGGTCCTCTGGAACACAGGGGCTCCAACGGGTTGTCTTGATCCTGC,TTTACAGGGGCTAGAGGGGTCAAGCTGTGCTCAGCCCAGAGGCAGCTGCCACACTTGCCAGCACCCCCCACTCAGTCACTATGTACAGATAAAGGGGCCTGCTTGGATCACCTTTTTCAAAGCCATCTGGCAGAGGCCATGGGGCTGTGTTGAAACCTGGGCTCCAGAGGCACTGCTGGGCCCATTACCCCTTGGCATCAGGTCCTCTGGAACACAGGGGCTCCAACGGGTTGTCTTGATCCTGC,,,52401117,C,,,,,1del,AATGATACGGCGACCACCGAGCAGGATCAAGACAACCCGTTGGAGCCCCTGTGTTCCAGAGGACCTGATGCCAAGGGGTAATGGGCCCAGCAGTGCCTCTGGAGCCCAGGTTTCAACACAGCCCCATGGCCTCTGCCAGATGGCTTTGAAAAAGGTGATCCAAGCAGGCCCCTTTATCTGTACATAGTGACTGAGTGGGGGGTCTGGCAAGTGTGGCAGCTGCCTCTGGGCTGAGCACAGCTTGACCCCTCTAGCCCCTGTAAATCGTATGCCGTCTTCTGCTTG
ENST00000460680.6.ENSG00000163930.10_chr3:52401118_1del_rc,homo sapiens,GRCh38,ENSG00000163930.10,ENST00000460680.6,chr3,-,52401056,52401300,1,TTTACAGGGGCTAGAGGGGTCAAGCTGTGCTCAGCCCAGAGGCAGCTGCCACACTTGCCAGCACCCCCCACTCAGTCACTATGTACAGATAAAGGGGCCTGCTTGGATCACCTTTTTCAAAGCCATCTGGCAGAGGCCATGGGGCTGTGTTGGGGCCTGGGCTCCAGAGGCACTGCTGGGCCCATTACCCCTTGGCATCAGGTCCTCTGGAACACAGGGGCTCCAACGGGTTGTCTTGATCCTGC,TTTACAGGGGCTAGAGGGGTCAAGCTGTGCTCAGCCCAGAGGCAGCTGCCACACTTGCCAGCACCCCCCACTCAGTCACTATGTACAGATAAAGGGGCCTGCTTGGATCACCTTTTTCAAAGCCATCTGGCAGAGGCCATGGGGCTGTGTTGAAACCTGGGCTCCAGAGGCACTGCTGGGCCCATTACCCCTTGGCATCAGGTCCTCTGGAACACAGGGGCTCCAACGGGTTGTCTTGATCCTGC,,,52401118,A,,,,,1del,AATGATACGGCGACCACCGAGCAGGATCAAGACAACCCGTTGGAGCCCCTGTGTTCCAGAGGACCTGATGCCAAGGGGTAATGGGCCCAGCAGTGCCTCTGGAGCCCAGGTTTCAACACAGCCCCATGGCCTCTGCCAGATGGCTTTGAAAAAGGTGATCCAAGCAGGCCCCTTTATCTGTACATAGTGACTGAGTGGGGGGGCTGGCAAGTGTGGCAGCTGCCTCTGGGCTGAGCACAGCTTGACCCCTCTAGCCCCTGTAAATCGTATGCCGTCTTCTGCTTG
```

### Variant file

VCF file containing a subset of the metadata in VCF format. The metadata are stored in the `INFO` field. The `REF` field reports the reference sequence including PAM protection edits.

The variants can be linked to the corresponding oligonucleotides via the `SGE_OLIGO` tag, and, for custom variants, to the original VCF files via the `SGE_VCF_ALIAS` and `SGE_VCF_VAR_ID` tags.

`INFO` tags:

|Tag|Metadata field|Description|
|-|-|-|
|`SGE_OLIGO`|`oligo_name`|Corresponding oligonucleotide name.|
|`SGE_SRC`|`mutator`|Variant source.|
|`SGE_REF`|`ref`|(Optional) Reference sequence, only if different from the PAM-protected reference sequence.|
|`SGE_VCF_ALIAS`|`vcf_alias`|(Optional) VCF variant identifier, only for `custom` variants.|
|`SGE_VCF_VAR_ID`|`vcf_var_id`|(Optional) VCF variant source file alias, only for `custom` variants.|

### Unique oligonucleotides file

Comma-separated values (CSV) file containing only the label and the sequence of the oligonucleotides generated for any given targeton, where the sequences are unique. This is a subset of the [oligonucleotide metadata file](#oligonucleotide-metadata-file) fields (`oligo_name` and `mseq`) and rows.

Example:

```
oligo_name,mseq
ENST00000256474.3.ENSG00000134086.8_chr3:10146513_G>A_snv,GGATTACAGGTGTGGGCCACCGTGCCCAGCCACCGGTGTGGCTCTTTAACAACCTTTGCTTGTCCCGATAAGTCACCTTTGGCTCTTCAGAGATGCAGGGACACACGATGGGCTTCTGGTTAACCAAACTGAATTATTTGTGCCATCTCTCAATGTTGACGGACAGCCTATTTTTGCCAATATCACACTGCCAGGTACTGACGTTTTACTTTTTAAAAAGATAAGGTTGTTGTGGTAAGTACAGG
ENST00000256474.3.ENSG00000134086.8_chr3:10146513_G>C_snv,GGATTACAGGTGTGGGCCACCGTGCCCAGCCACCGGTGTGGCTCTTTAACAACCTTTGCTTGTCCCGATACGTCACCTTTGGCTCTTCAGAGATGCAGGGACACACGATGGGCTTCTGGTTAACCAAACTGAATTATTTGTGCCATCTCTCAATGTTGACGGACAGCCTATTTTTGCCAATATCACACTGCCAGGTACTGACGTTTTACTTTTTAAAAAGATAAGGTTGTTGTGGTAAGTACAGG
ENST00000256474.3.ENSG00000134086.8_chr3:10146513_G>T_snv,GGATTACAGGTGTGGGCCACCGTGCCCAGCCACCGGTGTGGCTCTTTAACAACCTTTGCTTGTCCCGATATGTCACCTTTGGCTCTTCAGAGATGCAGGGACACACGATGGGCTTCTGGTTAACCAAACTGAATTATTTGTGCCATCTCTCAATGTTGACGGACAGCCTATTTTTGCCAATATCACACTGCCAGGTACTGACGTTTTACTTTTTAAAAAGATAAGGTTGTTGTGGTAAGTACAGG
ENST00000256474.3.ENSG00000134086.8_chr3:10146474_A_1del,GGATTACAGGTGTGGGCCACCGTGCCCAGCCCCGGTGTGGCTCTTTAACAACCTTTGCTTGTCCCGATAGGTCACCTTTGGCTCTTCAGAGATGCAGGGACACACGATGGGCTTCTGGTTAACCAAACTGAATTATTTGTGCCATCTCTCAATGTTGACGGACAGCCTATTTTTGCCAATATCACACTGCCAGGTACTGACGTTTTACTTTTTAAAAAGATAAGGTTGTTGTGGTAAGTACAGG
ENST00000256474.3.ENSG00000134086.8_chr3:10146475_C_1del,GGATTACAGGTGTGGGCCACCGTGCCCAGCCACGGTGTGGCTCTTTAACAACCTTTGCTTGTCCCGATAGGTCACCTTTGGCTCTTCAGAGATGCAGGGACACACGATGGGCTTCTGGTTAACCAAACTGAATTATTTGTGCCATCTCTCAATGTTGACGGACAGCCTATTTTTGCCAATATCACACTGCCAGGTACTGACGTTTTACTTTTTAAAAAGATAAGGTTGTTGTGGTAAGTACAGG
ENST00000256474.3.ENSG00000134086.8_chr3:10146477_G_1del,GGATTACAGGTGTGGGCCACCGTGCCCAGCCACCGTGTGGCTCTTTAACAACCTTTGCTTGTCCCGATAGGTCACCTTTGGCTCTTCAGAGATGCAGGGACACACGATGGGCTTCTGGTTAACCAAACTGAATTATTTGTGCCATCTCTCAATGTTGACGGACAGCCTATTTTTGCCAATATCACACTGCCAGGTACTGACGTTTTACTTTTTAAAAAGATAAGGTTGTTGTGGTAAGTACAGG
```

### Reference sequence retrieval quality check file

Comma-separated values (CSV) file with no header reporting the reference sequences as retrieved based on the genomic coordinates and extension vector provided in the [targeton file](#targeton-file).

The targeton name is derived from the genomic coordinates of the reference sequence.

|Field|Format|Description|
|-|-|-|
|(Targeton name)|`<CHR>_<START>_<END>_<STRAND>`|Name of the targeton.|
|(Reference genomic range)|`<CHR>:<START>-<END>`|Reference sequence region.|
|(5' constant region start)|integer|Start position of the 5' constant region.|
|(5' constant region sequence)|DNA sequence|Sequence of the 5' constant region.|
|(Target region 1 start)|integer|Start position of target region 1.|
|(Target region 1 sequence)|DNA sequence|Sequence of target region 1.|
|(Target region 2 start)|integer|Start position of target region 2.|
|(Target region 2 sequence)|DNA sequence|Sequence of target region 2.|
|(Target region 3 start)|integer|Start position of target region 3.|
|(Target region 3 sequence)|DNA sequence|Sequence of target region 3.|
|(3' constant region start)|integer|Start position of the 3' constant region.|
|(3' constant region sequence)|DNA sequence|Sequence of the 3' constant region.|

Example:

```
chr3_10146443_10146687_plus,chr3:10146443-10146687,10146443,GGATTACAGGTGTGGGCCACCGTGCCCAGCC,10146474,ACCGGTGTGGCTCTTTAACAACCTTTGCTTGTCCCGATAG,10146514,GTCACCTTTGGCTCTTCAGAGATGCAGGGACACACGATGGGCTTCTGGTTAACCAAACTGAATTATTTGTGCCATCTCTCAATGTTGACGGACAGCCTATTTTTGCCAATATCACACTGCCAG,10146637,GTACTGACGTTTTACTTTTTAAAAAGATAAGGTTG,10146672,TTGTGGTAAGTACAGG
```

## Development

To run the unit tests, install the extra requirements first:

```sh
cd tests
pip install -r unit_tests/requirements.txt
./run_unit_tests.sh
```

## LICENSE

```none
VaLiAnT, (c) 2020, GRL (the "Software")

The Software remains the property of Genome Research Ltd ("GRL").

The Software is distributed "AS IS" under this Licence solely for non-commercial use in the hope that it will be useful,
but in order that GRL as a charitable foundation protects its assets for the benefit of its educational and research
purposes, GRL makes clear that no condition is made or to be implied, nor is any warranty given or to be implied, as to
the accuracy of the Software, or that it will be suitable for any particular purpose or for use under any specific
conditions. Furthermore, GRL disclaims all responsibility for the use which is made of the Software. It further
disclaims any liability for the outcomes arising from using  the Software.

The Licensee agrees to indemnify GRL and hold GRL harmless from and against any and all claims, damages and liabilities
asserted by third parties (including claims for negligence) which arise directly or indirectly from the use of the
Software or the sale of any products based on the Software.

No part of the Software may be reproduced, modified, transmitted or transferred in any form or by any means, electronic
or mechanical, without the express permission of GRL. The permission of GRL is not required if the said reproduction,
modification, transmission or transference is done without financial return, the conditions of this Licence are imposed
upon the receiver of the product, and all original and amended source code is included in any transmitted product. You
may be held legally responsible for any copyright infringement that is caused or encouraged by your failure to abide by
these terms and conditions.

You are not permitted under this Licence to use this Software commercially. Use for which any financial return is
received shall be defined as commercial use, and includes (1) integration of all or part of the source code or the
Software into a product for sale or license by or on behalf of Licensee to third parties or (2) use of the Software
or any derivative of it for research with the final aim of developing software products for sale or license to a third
party or (3) use of the Software or any derivative of it for research with the final aim of developing non-software
products for sale or license to a third party, or (4) use of the Software to provide any service to an external
organisation for which payment is received. If you are interested in using the Software commercially, please contact
legal@sanger.ac.uk. Contact details are: legal@sanger.ac.uk quoting reference Valiant-software.
```

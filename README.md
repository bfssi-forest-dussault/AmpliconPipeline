# OLCAmpliconPipeline *(WIP)*

### Description

This program will take an OLC 16S MiSeq amplicon sequencing run and
process the output with QIIME 2. Currently, this is intended to be used
internally within the OLC R&D division.

### Installation Instructions

#### Dependencies

OLCAmpliconPipeline has dependencies on the following:

- QIIME 2 (v2017.11): _https://docs.qiime2.org/2017.11/install/native/_

In order to run this pipeline, the QIIME 2 conda environment must be activated.

i.e. `source activate qiime2-2017.11`

#### Download And Installation

To download this repository, use: `git clone https://github.com/forestdussault/AmpliconPipeline.git`

Executable scripts are found in `bin/`.

### Tests and Example Data

Basic tests can be found in `tests/`.

To run these tests, use: `pytest`

### Command Line Arguments

```
--inputdir
    Directory containing your raw MiSeq output (i.e. *.fastq.gz files)
--outdir
    Base directory for all output from AmpliconPipeline. Note that this directory must not already exist.
--metadata
    Path to existing QIIME2 tab-separated metadata file
--classifier
    Path to existing QIIME2 Classifier Artifact.
--verbose
    Set flag to enable more verbose output
```
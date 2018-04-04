# AmpliconPipeline

### Description

This program will take an OLC 16S MiSeq amplicon sequencing run and
process the output with QIIME 2. Currently, this is intended to be used
internally within the OLC R&D division.

### Installation Instructions

The AmpliconPipeline is distributed as a Docker image.
As a result, an installation of Docker is the only dependency.

To retrieve the Docker image:
```
docker pull forestdussault/ampliconpipeline:v0.9
```

### Running the pipeline
1. Interactively enter the AmpliconPipeline container
```
docker run -it --rm -v path/to/your/data:path/to/your/data ampliconpipeline:v0.9
```

2. Source the conda environment
```
source activate AmpliconPipeline
```

3. Get started with the following:
```
python cli.py --help
```


### Command Line Arguments

```
Usage: cli.py [OPTIONS]

Options:
  -i, --inputdir PATH      Directory containing your raw MiSeq output (files
                           must be *.fastq.gz)  [required]
  -o, --outdir PATH        Base directory for all output from
                           AmpliconPipeline. Note that this directory must NOT
                           already exist.  [required]
  -m, --metadata PATH      Path to QIIME2 tab-separated metadata file. This
                           must be a *.tsv file.  [required]
  -eq, --evaluate_quality  Setting this flag will only run the pipeline up
                           until generating the demux_summary.qzv file. This
                           is important to do before running the pipeline to
                           establish acceptable trimming/truncation parameters
                           to pass to dada2.
  -c, --classifier PATH    Path to a QIIME2 Classifier Artifact. By default
                           this will point to a previously trained V3-V4
                           classifier using SILVA taxonomy.
  -f, --filtering_flag     Set flag to only proceed to the filtering step of
                           analysis. This is useful for testing/optimizing
                           trimming parameters for a full run, or for
                           generating files to be merged for later analysis.
  -v, --verbose            Set this flag to enable more verbose output.
  --help                   Show this message and exit.
```

### Tests and Example Data

Basic tests can be found in `tests/`.

To run these tests, use: `pytest`

### Other notes
#### Classifier
By default, this pipeline uses a pre-trained classifier using the V3-V4 region.

The classifier and some additional details can be retrieved here:
https://figshare.com/articles/99_V3V4_Silva_naive_bayes_classifier_qza/6087197

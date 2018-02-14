 #!/usr/bin/env python3

import logging
import os
import click
from bin import helper_functions
from bin import qiime2_pipeline


@click.command()
@click.option('-i', '--inputdir',
              type=click.Path(exists=True),
              required=True,
              help='Directory containing your raw MiSeq output (i.e. *.fastq.gz files)')
@click.option('-o', '--outdir',
              type=click.Path(exists=False),
              required=True,
              help='Base directory for all output from AmpliconPipeline. '
                   'Note that this directory must not already exist')
@click.option('-m', '--metadata',
              type=click.Path(exists=True),
              required=True,
              help='Path to QIIME2 tab-separated metadata file. This file have the .tsv extension.')
@click.option('-eq','--evaluate_quality',
              is_flag=True,
              default=False,
              help='Setting this flag will only run the pipeline up until generating the demux_summary.qzv file. '
                   'This is important to do before running the pipeline to establish acceptable trimming/truncation '
                   'parameters to pass to dada2.')
@click.option('-c', '--classifier',
              type=click.Path(exists=True),
              required=False,
              help='Path to QIIME2 Classifier Artifact')
@click.option('-f', '--filtering_flag',
              is_flag=True,
              default=False,
              help='Set flag to only proceed to the filtering step of analysis')
@click.option('-v', '--verbose',
              is_flag=True,
              default=False,
              help='Set flag to enable more verbose output')
@click.pass_context
def cli(ctx, inputdir, outdir, metadata, classifier, evaluate_quality, filtering_flag, verbose):
    # Logging setup
    if verbose:
        logging.basicConfig(
            format='\033[92m \033[1m %(asctime)s \033[0m %(message)s ',
            level=logging.DEBUG,
            datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(
            format='\033[92m \033[1m %(asctime)s \033[0m %(message)s ',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')

    if evaluate_quality:
        logging.info('Starting QIIME2-QC Pipeline with output routing to {}'.format(outdir))
        data_artifact_path = helper_functions.project_setup(outdir=outdir, inputdir=inputdir)
        qiime2_pipeline.run_qc_pipeline(base_dir=os.path.join(outdir, 'qiime2'),
                                        data_artifact_path=data_artifact_path,
                                        sample_metadata_path=metadata)
        logging.info('\nQIIME2-QC Pipeline Completed')
        ctx.exit()

    logging.info('Starting QIIME2 Pipeline with output routing to {}'.format(outdir))

    # Input validation
    if classifier is None:
        click.echo(ctx.get_help(), err=True)
        click.echo('\nERROR: Please provide a path to an existing classifier. '
                   'Training is not yet implemented.', err=True)
        ctx.exit()

    if os.path.isdir(outdir):
        click.echo(ctx.get_help(), err=True)
        click.echo('\nERROR: Specified output directory already exists. '
                      'Please provide a new path that does not already exist.', err=True)
        ctx.exit()

    # Project setup + get path to data artifact
    data_artifact_path = helper_functions.project_setup(outdir=outdir, inputdir=inputdir)

    # Filtering flag
    if filtering_flag:
        logging.info('FILTERING_FLAG SET. Pipeline will only proceed to DADA2 step.')

    # Run the full pipeline
    qiime2_pipeline.run_pipeline(base_dir=os.path.join(outdir, 'qiime2'),
                                 data_artifact_path=data_artifact_path,
                                 sample_metadata_path=metadata,
                                 classifier_artifact_path=classifier,
                                 filtering_flag=filtering_flag)
    logging.info('\nQIIME2 Pipeline Completed')
    ctx.exit()


if __name__ == '__main__':
    cli()
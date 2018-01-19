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
              help='Base directory for all output from AmpliconPipeline. Note that this directory must not already exist.')
@click.option('-m', '--metadata',
              type=click.Path(exists=True),
              required=True,
              help='Path to QIIME2 tab-separated metadata file')
@click.option('-c', '--classifier',
              type=click.Path(exists=True),
              required=False,
              help='Path to QIIME2 Classifier Artifact')
@click.option('-v', '--verbose',
              is_flag=True,
              default=False,
              help='Set flag to enable more verbose output')
@click.pass_context
def cli(ctx, inputdir, outdir, metadata, classifier, verbose):
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

    # Input validation
    if classifier is None:
        click.echo(ctx.get_help(),
                   err=True)
        click.echo('\nERROR: Please provide a path to an existing classifier. '
                   'Training is not yet implemented.',
                   err=True)
        ctx.exit()

    if os.path.isdir(outdir):
        click.echo(ctx.get_help(),
                   err=True)
        click.echo('\nERROR: Specified output directory already exists. '
                      'Please provide a new path that does not already exist.',
                   err=True)
        ctx.exit()

    # Create folder structure
    os.mkdir(outdir)
    os.mkdir(os.path.join(outdir, 'data'))
    os.mkdir(os.path.join(outdir, 'qiime2'))
    logging.debug('Created QIIME 2 folder structure at {}'.format(outdir))

    # Prepare dictionary containing R1 and R2 for each sample ID
    sample_dictionary = helper_functions.get_sample_dictionary(inputdir)
    logging.debug('Sample Dictionary:{}'.format(sample_dictionary))

    # Create symlinks in data folder
    helper_functions.symlink_dictionary(sample_dictionary=sample_dictionary,
                                        destination_folder=os.path.join(outdir, 'data'))
    logging.debug('Creating symlinks within the following folder: {}'.format(os.path.join(outdir, 'data')))

    # Fix symlink filenames for Qiime 2
    helper_functions.append_dummy_barcodes(os.path.join(outdir, 'data'))
    logging.debug('Appended dummy barcodes successfully')

    # Call Qiime 2 to create artifact
    logging.info('Creating sample data artifact for QIIME 2')
    data_artifact_path = helper_functions.create_sampledata_artifact(datadir=os.path.join(outdir, 'data'),
                                                                     qiimedir=os.path.join(outdir, 'qiime2'))

    # Run the full pipeline
    logging.info('Starting QIIME2 Pipeline with output routing to {}'.format(outdir))
    qiime2_pipeline.run_pipeline(base_dir=os.path.join(outdir, 'qiime2'),
                                 data_artifact_path=data_artifact_path,
                                 sample_metadata_path=metadata,
                                 classifier_artifact_path=classifier)
    logging.info('\nQIIME2 Pipeline Completed')


if __name__ == '__main__':
    cli()
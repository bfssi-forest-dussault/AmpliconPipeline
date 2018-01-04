 #!/usr/bin/env python3


import logging
import os
import click
from bin import helper_functions
from bin import qiime2_pipeline


@click.command()
@click.option('--inputdir', default=None, help='Directory containing your raw MiSeq output (i.e. *.fastq.gz files)')
@click.option('--outdir', default=None, help='Base directory for all output from AmpliconPipeline')
@click.option('--metadata', default=None, help='Path to QIIME2 tab-separated metadata file')
@click.option('--classifier', default=None, help='Path to QIIME2 Classifier Artifact')
@click.option('--verbose', is_flag=True, help='Set flag to enable more verbose output')
def cli(inputdir, outdir, metadata, classifier, verbose):
    # Logging setup
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Input validation
    if inputdir is None or outdir is None or metadata is None or classifier is None:
        logging.error('Please provide inputdir, outdir, metadata, and classifier paths')
        quit()

    if os.path.isdir(outdir):
        logging.error('Specified output directory already exists. '
                      'Please provide a new name for your desired output directory')
        quit()

    # Create folder structure
    os.mkdir(outdir)
    os.mkdir(os.path.join(outdir, 'data'))
    os.mkdir(os.path.join(outdir, 'qiime2'))
    logging.debug('Created folder structure')

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
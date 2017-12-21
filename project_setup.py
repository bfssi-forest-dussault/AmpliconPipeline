import os
import glob
import click
import logging
import subprocess
import qiime2 as q2

logging.basicConfig(level=logging.DEBUG)


def retrieve_fastqgz(directory):
    fastq_file_list = glob.glob(os.path.join(directory, '*.fastq.gz'))
    return fastq_file_list


def execute_command(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.decode('ascii'), err.decode('ascii')


def retrieve_unique_sampleids(fastq_file_list):
    # Iterate through all of the fastq files and grab the sampleID, append to list
    sample_id_list = list()
    for file in fastq_file_list:
        if valid_olc_id(file):
            sample_id = os.path.basename(file)[:13]  # WARNING: This is specific to the OLC naming scheme
            sample_id_list.append(sample_id)
    # Get unique sample IDs
    sample_id_list = list(set(sample_id_list))
    return sample_id_list


def get_readpair(sample_id, fastq_file_list):
    R1, R2 = None, None
    for file in fastq_file_list:
        if sample_id in os.path.basename(file):
            if 'R1' in os.path.basename(file):
                R1 = file
            elif 'R2' in os.path.basename(file):
                R2 = file
    if R1 is not None:
        return [os.path.abspath(R1), os.path.abspath(R2)]
    else:
        logging.debug('Could not pair {}'.format(sample_id))


def populate_sample_dictionary(sample_id_list, fastq_file_list):
    # Find file pairs for each unique sample ID
    sample_dictionary = {}
    for sample_id in sample_id_list:
        read_pair = get_readpair(sample_id, fastq_file_list)
        sample_dictionary[sample_id] = read_pair
    return sample_dictionary


def get_sample_dictionary(directory):
    fastq_file_list = retrieve_fastqgz(directory)
    sample_id_list = retrieve_unique_sampleids(fastq_file_list)
    sample_dictionary = populate_sample_dictionary(sample_id_list, fastq_file_list)
    return sample_dictionary


def valid_olc_id(filename):
    """
    Validate that a fastq.gz file contains a valid OLC sample id
    """
    sample_id = os.path.basename(filename)[:13]
    id_components = sample_id.split('-')
    valid_status = False
    if id_components[0].isdigit() and id_components[1] == 'SEQ' and id_components[2].isdigit():
        valid_status = True
    else:
        logging.debug('ID for {} is not a valid OLC ID'.format(sample_id))
    return valid_status


def append_dummy_barcodes(path):
    """
    Function to append a dummy barcode _00 to all .fastq.gz MiSeq read files for compatibility with QIIME 2
    CasavaOneEightSingleLanePerSampleDirFmt
    """
    for file in retrieve_fastqgz(path):
        if valid_olc_id(file):
            os.rename(os.path.abspath(file), os.path.abspath(file).replace('_S', '_00_S'))
    logging.info('Renamed all valid OLC *.fastq.gz files in {}'.format(path))

def create_symlink(target, destination_folder):
    os.symlink(target, os.path.join(destination_folder, os.path.basename(target)))


def symlink_dictionary(sample_dictionary, destination_folder):
    for key, value in sample_dictionary.items():
        try:
            create_symlink(value[0], destination_folder)
            create_symlink(value[1], destination_folder)
            logging.info('Created symlinks for {}'.format(key))
        except:
            logging.error('Symbolic links to read pair {} already exist.'.format(key))


def create_sampledata_artifact(datadir, qiimedir):
    cmd = "qiime tools import " \
          "--type 'SampleData[PairedEndSequencesWithQuality]' " \
          "--input-path {datadir} " \
          "--output-path {qiimeout} " \
          "--source-format CasavaOneEightSingleLanePerSampleDirFmt".format(datadir=datadir,
                                                                           qiimeout=os.path.join(qiimedir,'paired-sample-data.qza'))
    out, err = execute_command(cmd)

    logging.info('STDOUT:{}'.format(out))
    logging.info('STDERR:{}'.format(err))
    logging.info('Successfully created QIIME 2 data Artifact.')

    return os.path.join(qiimedir,'paired-sample-data.qza')

@click.command()
@click.option('--inputdir', help='Directory containing your raw MiSeq output (i.e. *.fastq.gz files)')
@click.option('--outdir', help='Base directory for all output from AmpliconPipeline')
def main(inputdir=None, outdir=None):

    # Input validation
    if inputdir is None and outdir is None:
        logging.error('Please provide an input directory and working directory.')
        quit()

    if os.path.isdir(outdir):
        logging.error('Output directory already exists. Please provide a new name for your desired output directory.')
        quit()

    # Create folder structure
    os.mkdir(outdir)
    os.mkdir(os.path.join(outdir, 'data'))
    os.mkdir(os.path.join(outdir, 'qiime2'))

    # Prepare dictionary containing R1 and R2 for each sample ID
    sample_dictionary = get_sample_dictionary(inputdir)

    # Create symlinks in data folder
    symlink_dictionary(sample_dictionary=sample_dictionary,
                       destination_folder=os.path.join(outdir, 'data'))

    # Fix symlink filenames for Qiime 2
    append_dummy_barcodes(os.path.join(outdir, 'data'))

    # Call Qiime 2 to create artifact
    create_sampledata_artifact(datadir=os.path.join(outdir, 'data'),
                               qiimedir=os.path.join(outdir, 'qiime2'))


if __name__ == '__main__':
    main()
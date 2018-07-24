import logging
import click
import os

import qiime2

from pathlib import Path
from bin import helper_functions
from bin import qiime2_pipeline
from bin.helper_functions import execute_command_simple

from qiime2 import Metadata
from qiime2.plugins import feature_classifier


@click.command()
@click.option('-i', '--inputfasta',
              type=click.Path(exists=True),
              required=True,
              help='Path to .fasta file containing reference sequences for OTUs. e.g. 99_otus.fasta')
@click.option('-t', '--taxonomytext',
              type=click.Path(exists=True),
              required=True,
              help='Path to .txt file containing taxonomy information for OTUs. e.g. 99_otu_taxonomy.txt')
@click.option('-o', '--outdir',
              type=click.Path(exists=False),
              required=True,
              help='Base directory to drop output from the classifier. '
                   'Note that this directory must NOT already exist.')
@click.option('-f', '--forward_primer',
              type=click.STRING,
              default=None,
              required=True,
              help='Sequence for forward primer')
@click.option('-r', '--reverse_primer',
              type=click.STRING,
              default=None,
              required=True,
              help='Sequence for reverse primer')
@click.pass_context
def cli(ctx, inputfasta, taxonomytext, outdir, forward_primer, reverse_primer):
    # Convert to PosixPath objects
    inputfasta = Path(inputfasta)
    taxonomytext = Path(taxonomytext)
    outdir = Path(outdir)

    # Output directory validation
    try:
        os.makedirs(str(outdir), exist_ok=False)
    except FileExistsError:
        logging.error("ERROR: Output directory already exists.")
        quit()

    otu_filepath = output_otu_qza(outdir=outdir, inputfasta=inputfasta)
    reference_taxonomy_filepath = output_ref_taxonomy_qza(outdir=outdir, inputtxt=taxonomytext)
    ref_seqs, ref_seqs_qza = extract_reads(otu_qza=otu_filepath, f_primer=forward_primer, r_primer=reverse_primer,
                                           outdir=outdir)
    train_feature_classifier(reference_seqs=ref_seqs, reference_taxonomy_filepath=reference_taxonomy_filepath)


def output_otu_qza(outdir: Path, inputfasta: Path) -> Path:
    outfile = outdir / inputfasta.with_suffix(".qza").name
    cmd = "qiime tools import " \
          "--type 'FeatureData[Sequence]' " \
          "--input-path {inputfasta} " \
          "--output-path {outfile}".format(inputfasta=inputfasta, outfile=outfile)
    execute_command_simple(cmd)
    return outfile


def output_ref_taxonomy_qza(outdir: Path, inputtxt: Path):
    outfile = outdir / inputtxt.with_suffix(".qza").name
    cmd = "qiime tools import " \
          "--type 'FeatureData[Taxonomy]' " \
          "--source-format HeaderlessTSVTaxonomyFormat " \
          "--input-path {inputtxt} " \
          "--output-path {outfile}".format(inputtxt=inputtxt, outfile=outfile)
    execute_command_simple(cmd)
    return outfile


def extract_reads(otu_qza: Path, f_primer: str, r_primer: str, outdir: Path) -> tuple:
    outfile = outdir / 'ref-seqs.qza'
    otus = qiime2.Artifact.load(otu_qza)
    reference_seqs = feature_classifier.methods.extract_reads(sequences=otus,
                                                              f_primer=f_primer,
                                                              r_primer=r_primer)
    reference_seqs.reads.save(outfile)
    return reference_seqs, outfile


def train_feature_classifier(reference_seqs, reference_taxonomy_filepath):
    """
    Trains a Naive Bayes classifier based on a reference database/taxonomy

    Primers for V3-V4 region:
    F: S-D-Bact-0341-b-S-17, 5′-CCTACGGGNGGCWGCAG-3′,
    R: S-D-Bact-0785-a-A-21, 5′-GACTACHVGGGTATCTAATCC-3
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3592464/

    Primers for Schloss MiSeq protocol (V4):
    F: TATGGTAATTGTGTGCCAGCMGCCGCGGTAA
    R: AGTCAGTCAGCCGGACTACHVGGGTWTCTAAT

    :param base_dir: Main working directory filepath
    :param otu_filepath: File path to reference OTU .qza file
    :param reference_taxonomy_filepath: File path to reference taxonomy .qza file
    :param f_primer: String containing forward primer sequence
    :param r_primer: String containing reverse primer sequence
    :return: Returns the trained feature classifier
    """

    ref_taxonomy = qiime2.Artifact.load(reference_taxonomy_filepath)
    naive_bayes_classifier = feature_classifier.methods.fit_classifier_naive_bayes(reference_reads=reference_seqs.reads,
                                                                                   reference_taxonomy=ref_taxonomy)
    return naive_bayes_classifier


if __name__ == "__main__":
    cli()

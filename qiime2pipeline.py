import os
import inspect
import logging
import multiprocessing
import qiime2
from qiime2.plugins import feature_table, \
    dada2, \
    demux, \
    metadata, \
    alignment, \
    phylogeny, \
    diversity, \
    emperor, \
    feature_classifier, \
    taxa


def load_data_artifact(filepath):
    data_artifact = qiime2.Artifact.load(filepath)
    return data_artifact


def load_sample_metadata(filepath):
    metadata_object = qiime2.Metadata.load(filepath)
    return metadata_object


def visualize_metadata(base_dir, metadata_object):
    metadata_viz_filename = os.path.join(base_dir, 'sample-metadata-tabulate')
    metadata_viz = metadata.visualizers.tabulate(metadata_object)
    metadata_viz.visualization.save(metadata_viz_filename)
    logging.debug('Saved {} successfully'.format(metadata_viz_filename))


def visualize_demux(base_dir, data_artifact):
    demux_summary_filename = os.path.join(base_dir, 'demux_summary.qzv')
    demux_viz = demux.visualizers.summarize(data=data_artifact)
    demux_viz.visualization.save(demux_summary_filename)
    logging.debug('Saved {} successfully'.format(demux_summary_filename))


def run_dada2(base_dir, demultiplexed_seqs, trim_left_f=10, trim_left_r=10, trunc_len_f=0, trunc_len_r=260, chimera_method='consensus', cpu_count=None):
    if cpu_count is None:
        cpu_count = multiprocessing.cpu_count()
    (dada2_filtered_table, dada2_filtered_rep_seqs) = dada2.methods.denoise_paired(demultiplexed_seqs=demultiplexed_seqs,
                                                                                   trim_left_f=trim_left_f,
                                                                                   trim_left_r=trim_left_r,
                                                                                   trunc_len_f=trunc_len_f,
                                                                                   trunc_len_r=trunc_len_r,
                                                                                   chimera_method=chimera_method,
                                                                                   n_threads=cpu_count)
    dada2_filtered_table.save(os.path.join(base_dir, 'table-dada2.qza'))
    dada2_filtered_rep_seqs.save(os.path.join(base_dir, 'rep-seqs-dada2.qza'))

    return dada2_filtered_table, dada2_filtered_rep_seqs

def visualize_dada2(base_dir, dada2_filtered_table, dada2_filtered_rep_seqs, metadata_object):
    feature_table_summary = feature_table.visualizers.summarize(table=dada2_filtered_table,
                                                                sample_metadata=metadata_object)
    feature_table_seqs = feature_table.visualizers.tabulate_seqs(data=dada2_filtered_rep_seqs)
    feature_table_summary.visualization.save(os.path.join(base_dir, 'table-dada2-summary.qzv'))
    feature_table_seqs.visualization.save(os.path.join(base_dir, 'rep-seqs-summary.qzv'))

data_artifact = load_data_artifact('/home/dussaultf/PycharmProjects/AmpliconPipeline/tests/sample_outdir/qiime2/paired-sample-data.qza')
base_dir = os.path.dirname('/home/dussaultf/PycharmProjects/AmpliconPipeline/tests/sample_outdir/qiime2/paired-sample-data.qza')
metadata_object = load_sample_metadata('/home/dussaultf/PycharmProjects/AmpliconPipeline/tests/sample_outdir/qiime2/sample-metadata.tsv')
visualize_metadata(base_dir, metadata_object)
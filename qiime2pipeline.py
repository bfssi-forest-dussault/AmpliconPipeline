import os
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
    # Path setup
    export_path = os.path.join(base_dir, 'sample-metadata-tabulate')

    # Prepare and save metadata visualization
    metadata_viz = metadata.visualizers.tabulate(metadata_object)
    metadata_viz.visualization.save(export_path)
    logging.info('Saved {} successfully'.format(export_path))

    return metadata_viz

def visualize_demux(base_dir, data_artifact):
    # Path setup
    export_path = os.path.join(base_dir, 'demux_summary.qzv')

    # Prepare and save demux summary visualization
    demux_viz = demux.visualizers.summarize(data=data_artifact)
    demux_viz.visualization.save(export_path)
    logging.info('Saved {} successfully'.format(export_path))

    return demux_viz

def dada2_qc(base_dir, demultiplexed_seqs, trim_left_f=10, trim_left_r=10, trunc_len_f=0, trunc_len_r=260, chimera_method='consensus', cpu_count=None):
    # Grab all CPUs if parameter is not specified
    if cpu_count is None:
        cpu_count = multiprocessing.cpu_count()

    # Run dada2
    (dada2_filtered_table, dada2_filtered_rep_seqs) = dada2.methods.denoise_paired(demultiplexed_seqs=demultiplexed_seqs,
                                                                                   trim_left_f=trim_left_f,
                                                                                   trim_left_r=trim_left_r,
                                                                                   trunc_len_f=trunc_len_f,
                                                                                   trunc_len_r=trunc_len_r,
                                                                                   chimera_method=chimera_method,
                                                                                   n_threads=cpu_count)

    # Save artifacts
    dada2_filtered_table.save(os.path.join(base_dir, 'table-dada2.qza'))
    dada2_filtered_rep_seqs.save(os.path.join(base_dir, 'rep-seqs-dada2.qza'))
    logging.info('Completed running dada2.')

    return dada2_filtered_table, dada2_filtered_rep_seqs


def visualize_dada2(base_dir, dada2_filtered_table, dada2_filtered_rep_seqs, metadata_object):
    # Prepare feature table
    feature_table_summary = feature_table.visualizers.summarize(table=dada2_filtered_table,
                                                                sample_metadata=metadata_object)

    # Prepare sequence table
    feature_table_seqs = feature_table.visualizers.tabulate_seqs(data=dada2_filtered_rep_seqs)

    # Save visualizations
    feature_table_summary.visualization.save(os.path.join(base_dir, 'table-dada2-summary.qzv'))
    feature_table_seqs.visualization.save(os.path.join(base_dir, 'rep-seqs-summary.qzv'))
    logging.info('Saved dada2 visualizations successfully.')

    return feature_table_summary

def seq_alignment_mask(base_dir, dada2_filtered_rep_seqs, cpu_count=None):
    # CPU setup
    if cpu_count is None:
        cpu_count = multiprocessing.cpu_count()

    # Path setup
    aligned_export_path = os.path.join(base_dir, 'aligned-rep-seqs.qza')
    mask_export_path = os.path.join(base_dir, 'masked-aligned-rep-seqs.qza')

    # Perform and save sequence alignment
    seq_alignment = alignment.methods.mafft(sequences=dada2_filtered_rep_seqs, n_threads=cpu_count)
    seq_alignment.alignment.save(aligned_export_path)
    logging.info('Saved {} successfully'.format(aligned_export_path))

    # Perform and save alignment mask
    seq_mask = alignment.methods.mask(alignment=seq_alignment.alignment)
    seq_mask.masked_alignment.save(mask_export_path)
    logging.info('Saved {} successfully'.format(mask_export_path))

    return seq_mask, seq_alignment


def phylo_tree(base_dir, seq_mask):
    # Path setup
    unrooted_export_path = os.path.join(base_dir, 'unrooted-tree.qza')
    rooted_export_path = os.path.join(base_dir, 'rooted-tree.qza')

    # Run and save unrooted tree
    phylo_unrooted_tree = phylogeny.methods.fasttree(alignment=seq_mask.masked_alignment)
    phylo_unrooted_tree.tree.save(unrooted_export_path)
    logging.info('Saved {} successfully'.format(unrooted_export_path))

    # Run and save rooted tree
    phylo_rooted_tree = phylogeny.methods.midpoint_root(tree=phylo_unrooted_tree.tree)
    phylo_rooted_tree.rooted_tree.save(rooted_export_path)
    logging.info('Saved {} successfully'.format(rooted_export_path))

    return phylo_unrooted_tree, phylo_rooted_tree


def export_newick(base_dir, tree):
    # Path setup
    export_path = os.path.join(base_dir, 'newick.tree')

    # Export data
    tree.rooted_tree.export_data(export_path)
    logging.info('Exported tree file in newick format from the follwing artifact: {}'.format(tree))

    return export_path


def load_classifier_artifact(classifier_artifact_path):
    # Load existing artifact
    naive_bayes_classifier = qiime2.Artifact.load(classifier_artifact_path)

    return naive_bayes_classifier


def alpha_rarefaction_visualization(base_dir, dada2_filtered_table, max_depth=50000):
    # Path setup
    alpha_rarefaction_export_path = os.path.join(base_dir, 'alpha-rarefaction.qzv')

    # Produce rarefaction curve
    alpha_rarefaction_viz = diversity.visualizers.alpha_rarefaction(table=dada2_filtered_table,
                                                                    max_depth=max_depth)

    # Save
    alpha_rarefaction_viz.visualization.save(alpha_rarefaction_export_path)

    return alpha_rarefaction_viz

def classify_taxonomy(base_dir, dada2_filtered_rep_seqs, classifier):
    # Path setup
    export_path = os.path.join(base_dir, 'taxonomy.qza')

    # Classify reads
    taxonomy_analysis = feature_classifier.methods.classify_sklearn(reads=dada2_filtered_rep_seqs,
                                                                    classifier=classifier)
    # Save the resulting artifact
    taxonomy_analysis.classification.save(export_path)
    logging.info('Saved {} successfully'.format(export_path))

    return taxonomy_analysis


def visualize_taxonomy(base_dir, metadata_object, taxonomy_analysis, dada2_filtered_table):
    # Path setup
    tax_export_path = os.path.join(base_dir, 'taxonomy.qzv')
    barplot_export_path = os.path.join(base_dir, 'taxonomy_barplot.qzv')

    # Load metadata
    taxonomy_metadata = qiime2.Metadata.from_artifact(taxonomy_analysis.classification)

    # Create taxonomy visualization
    taxonomy_visualization = metadata.visualizers.tabulate(taxonomy_metadata)

    # Save taxonomy visualization
    taxonomy_visualization.visualization.save(tax_export_path)
    logging.info('Saved {} successfully'.format(tax_export_path))

    # Create and save barplot visualization
    taxonomy_barplot = taxa.visualizers.barplot(table=dada2_filtered_table,
                                                taxonomy=taxonomy_analysis.classification,
                                                metadata=metadata_object)
    taxonomy_barplot.visualization.save(barplot_export_path)
    logging.info('Saved {} successfully'.format(barplot_export_path))

    return taxonomy_metadata


def run_diversity_metrics(base_dir, dada2_filtered_table, phylo_rooted_tree, metadata_object, sampling_depth=15000):
    # Path setup
    bray_curtis_path = os.path.join(base_dir, 'bray_curtis_emperor.qzv')
    jaccard_emperor_path = os.path.join(base_dir, 'jaccard_emperor.qzv')
    unweighted_unifrac_emperor_path = os.path.join(base_dir, 'unweighted_unifrac_emperor.qzv')
    weighted_unifrac_emperor_path = os.path.join(base_dir, 'weighted_unifrac_emperor.qzv')

    faith_visualization_path = os.path.join(base_dir, 'faith-pd-group-significance.qzv')
    evenness_visualization_path = os.path.join(base_dir, 'evenness-group-significance.qzv')
    beta_visualization_path = os.path.join(base_dir, 'unweighted-unifrac-sample-type-significance.qzv')

    # Retrieve diversity metrics
    diversity_metrics = diversity.pipelines.core_metrics_phylogenetic(table=dada2_filtered_table,
                                                                      phylogeny=phylo_rooted_tree.rooted_tree,
                                                                      sampling_depth=sampling_depth,
                                                                      metadata=metadata_object)

    # Save
    diversity_metrics.bray_curtis_emperor.save(bray_curtis_path)
    diversity_metrics.jaccard_emperor.save(jaccard_emperor_path)
    diversity_metrics.unweighted_unifrac_emperor.save(unweighted_unifrac_emperor_path)
    diversity_metrics.weighted_unifrac_emperor.save(weighted_unifrac_emperor_path)

    # Alpha group significance
    alpha_group_faith = diversity.visualizers.alpha_group_significance(alpha_diversity=diversity_metrics.faith_pd_vector,
                                                                 metadata=metadata_object)


    alpha_group_evenness = diversity.visualizers.alpha_group_significance(alpha_diversity=diversity_metrics.evenness_vector,
                                                                 metadata=metadata_object)

    # Save
    alpha_group_faith.visualization.save(faith_visualization_path)
    alpha_group_evenness.visualization.save(evenness_visualization_path)

    # Beta group significance
    beta_group = diversity.visualizers.beta_group_significance(
        distance_matrix=diversity_metrics.unweighted_unifrac_distance_matrix,
        metadata=metadata_object.get_category('#SampleID'),
        pairwise=True)
    beta_group.visualization.save(beta_visualization_path)

    return diversity_metrics


# TODO: Implement this.
def train_feature_classifier(base_dir, otu_filepath, reference_taxonomy_filepath, f_primer='CCTACGGGNGGCWGCAG', r_primer='GACTACHVGGGTATCTAATCC'):
    """
    Trains a Naive Bayes classifier based on a reference database/taxonomy
    :param base_dir: Main working directory filepath
    :param otu_filepath: File path to reference OTU .qza file
    :param reference_taxonomy_filepath: File path to reference taxonomy .qza file
    :param f_primer: String containing forward primer sequence. Default V3-V4 regions.
    :param r_primer: String containing reverse primer sequence Default V3-V4 regions.
    :return: Returns the trained feature classifier
    """

    # Path setup
    ref_seqs_filepath = os.path.join(base_dir, 'ref-seqs.qza')

    otus = qiime2.Artifact.load(otu_filepath)
    ref_taxonomy = qiime2.Artifact.load(reference_taxonomy_filepath)
    reference_seqs = feature_classifier.methods.extract_reads(sequences=otus,
                                                              f_primer=f_primer,
                                                              r_primer=r_primer)
    reference_seqs.reads.save(ref_seqs_filepath)
    naive_bayes_classifier = feature_classifier.methods.fit_classifier_naive_bayes(reference_reads=reference_seqs.reads,
                                                                                   reference_taxonomy=ref_taxonomy)

    return naive_bayes_classifier


def run_pipeline(base_dir, data_artifact_path, sample_metadata_path, classifier_artifact_path):
    # Load seed objects
    data_artifact = load_data_artifact(data_artifact_path)
    metadata_object = load_sample_metadata(sample_metadata_path)

    # Visualize metadata
    metadata_viz = visualize_metadata(base_dir=base_dir, metadata_object=metadata_object)

    # Demux
    demux_viz = visualize_demux(base_dir=base_dir, data_artifact=data_artifact)

    # Filter & denoise w/dada2
    (dada2_filtered_table, dada2_filtered_rep_seqs) = dada2_qc(base_dir=base_dir,
                                                               demultiplexed_seqs=data_artifact)
    # Visualize dada2
    feature_table_summary = visualize_dada2(base_dir=base_dir,
                                            dada2_filtered_table=dada2_filtered_table,
                                            dada2_filtered_rep_seqs=dada2_filtered_rep_seqs,
                                            metadata_object=metadata_object)

    # Mask and alignment
    (seq_mask, seq_alignment) = seq_alignment_mask(base_dir=base_dir,
                                                   dada2_filtered_rep_seqs=dada2_filtered_rep_seqs)

    # Phylogenetic tree
    (phylo_unrooted_tree, phylo_rooted_tree) = phylo_tree(base_dir=base_dir, seq_mask=seq_mask)

    # Export tree
    export_newick(base_dir=base_dir, tree=phylo_rooted_tree)

    # Load classifier
    naive_bayes_classifier = load_classifier_artifact(classifier_artifact_path=classifier_artifact_path)

    # Produce rarefaction visualization
    alpha_rarefaction_viz = alpha_rarefaction_visualization(base_dir=base_dir,
                                                            dada2_filtered_table=dada2_filtered_table)

    # Run taxonomic analysis
    taxonomy_analysis = classify_taxonomy(base_dir=base_dir,
                                          dada2_filtered_rep_seqs=dada2_filtered_rep_seqs,
                                          classifier=naive_bayes_classifier)

    # Visualize taxonomy
    taxonomy_metadata = visualize_taxonomy(base_dir=base_dir,
                                           metadata_object=metadata_object,
                                           taxonomy_analysis=taxonomy_analysis,
                                           dada2_filtered_table=dada2_filtered_table)

    # Alpha and beta diversity
    diversity_metrics = run_diversity_metrics(base_dir=base_dir,
                                              dada2_filtered_table=dada2_filtered_table,
                                              phylo_rooted_tree=phylo_rooted_tree,
                                              metadata_object=metadata_object)

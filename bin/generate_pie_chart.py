import os
import glob
import qiime2
import shutil
import click
import random
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

from collections import OrderedDict


# TODO: Make this less bad and also able to support genus, species, etc. instead of only family
def extract_family(value):
    try:
        family = value.split('D_4__')[1]
        if family == '':
            family = 'D_3: ' + value.split('D_3__')[1].replace('D_4__', '')
    except:
        family = value
    return family


def convert_to_percentages(df, cols):
    df[cols] = df[cols].div(df[cols].sum(axis=0), axis=1).multiply(100)
    return df


def get_column_pair(df, col1, col2):
    # Filter columns
    df = df.filter([col1, col2], axis=1)

    # Sort
    df = df.sort_values(col1)
    return df


def prepare_df_family(filepath, index_col):
    df = pd.read_csv(filepath, index_col=index_col)

    # Remove all extraneous columns
    df = df.drop((x for x in df.columns.tolist() if x.startswith('D_0__') is False), axis=1)

    # Transpose
    df = df.transpose()
    df = df.reset_index()

    # Create family column
    df['family'] = df['index'].map(extract_family)

    # Columns to target for conversion to percentage
    columns_to_target = [x for x in df.columns.tolist() if x not in ['index', 'family']]

    # Convert
    df = convert_to_percentages(df, columns_to_target)

    return df


def fixed_df(filename, index='sample_annotation'):
    df = prepare_df_family(filename, index)
    new_filename = filename.replace('.csv', '_temp.csv')

    # Stupid hack
    df.to_csv(new_filename, index=None)
    df = pd.read_csv(new_filename, index_col='family').fillna('NA')

    # Cleanup
    os.remove(new_filename)
    return df


def load_visualization(filepath):
    """
    :param filepath: path to qiime2 visualization
    :return: qiime2 object containing all information on viz
    """
    data_visualization = qiime2.Visualization.load(filepath)
    return data_visualization


def prepare_plot(df, sampleid):
    labels = []
    values = []
    ordered_dict = df.to_dict(into=OrderedDict)[sampleid]
    ordered_dict = OrderedDict(sorted(ordered_dict.items(), key=lambda x: x[1], reverse=True))
    explode = [0 for x in range(len(ordered_dict))]
    explode[0] = 0.1
    explode[1] = 0.1
    explode[2] = 0.1
    explode = tuple(explode)

    # ONLY SHOW LABELS FOR VALUES > 2%. Any change here should be mirrored in my_autopct() as well!
    for key, value in ordered_dict.items():
        values.append(value)
        if value > 2:
            labels.append(key)
        else:
            labels.append('')
    return values, labels, explode


def style_wedges(wedges, colordict):
    # Wedges
    for wedge in wedges[0]:
        wedge.set_color('black')
        try:
            wedge.set_facecolor(colordict[wedge.get_label()])
        except KeyError:
            wedge.set_facecolor(colordict[random.sample(list(colordict), 1)[0]])


def paired_pie_charts(values1, labels1, explode1, sample1, values2, labels2, explode2, sample2, out_dir):
    # Style setup
    plt.style.use('fivethirtyeight')

    # Consistent colouring across families
    colordict = generate_family_color_dict()

    # Font size
    mpl.rcParams['font.size'] = 9.5

    # Setup figure canvas
    fig = plt.figure(figsize=(24, 16))
    fig.suptitle('16S Composition Comparison', fontsize=14, horizontalalignment='center', x=0.275, y=0.92)

    ax1 = plt.subplot2grid((3, 4), (0, 0))
    wedges1 = ax1.pie(values1, labels=labels1, autopct=my_autopct, startangle=90, explode=explode1, shadow=False)
    style_wedges(wedges=wedges1, colordict=colordict)

    ax1.axis('equal')
    plt.title(sample1)

    ax2 = plt.subplot2grid((3, 4), (0, 1))

    wedges2 = ax2.pie(values2, labels=labels2, autopct=my_autopct, startangle=90, explode=explode2, shadow=False)
    style_wedges(wedges=wedges2, colordict=colordict)

    ax2.axis('equal')
    plt.title(sample2)

    outfile = os.path.join(out_dir, '{}_{}_plot.png'.format(sample1, sample2))
    plt.savefig(outfile, bbox_inches='tight')


def create_paired_pie_wrapper(filename, out_dir, sample1, sample2):
    df = fixed_df(filename)
    (values1, labels1, explode1) = prepare_plot(df, sample1)
    (values2, labels2, explode2) = prepare_plot(df, sample2)
    paired_pie_charts(values1, labels1, explode1, sample1, values2, labels2, explode2, sample2, out_dir)


def my_autopct(pct):
    return (('%.2f' % pct) + '%') if pct > 2 else ''


def generate_family_color_dict():
    file = open('/home/dussaultf/Documents/qiime2/graphing_taxonomic_output/color_list.txt', 'r')
    color_list = file.readlines()
    color_list = [x.strip() for x in color_list]

    families = glob.glob('/mnt/nas/Databases/GenBank/typestrains/Bacteria/*/*/*/*')
    families = [os.path.basename(x) for x in families]

    curated_families = []
    for family in families:
        if family.endswith('eae'):
            curated_families.append(family)
    color_list = color_list[:len(curated_families)]

    colordict = {}
    for l, c in zip(curated_families, color_list):
        colordict[l] = c

    return colordict


def extract_family_csv(input_path, output_path):
    """
    Output path is direct path to CSV file to create. This is really broken for some weird reason.
    """
    # Load visualization file
    try:
        qzv = load_visualization(input_path)
        print('Loaded {}'.format(qzv))
    except:
        print('Could not load .qzv file. Quitting.')
        return None

    # Create temporary directory to dump contents into
    temp_dir = os.path.join(os.path.dirname(output_path), 'temporary_qiime2_extraction')

    try:
        os.mkdir(temp_dir)
    except:
        shutil.rmtree(temp_dir)
        os.mkdir(temp_dir)

    # Grab CSV
    qzv.export_data(temp_dir)
    family_csv_path = os.path.join(temp_dir, 'level-5.csv')

    # Move file
    os.rename(family_csv_path, output_path)

    # Cleanup
    shutil.rmtree(temp_dir)

    return output_path


# TODO: Implement taxonomic_level and filter
@click.command()
@click.option('-i', '--input_file',
              type=click.Path(exists=True),
              required=True,
              help='CSV file exported from taxonomy_barplot visualization (*.qzv)')
@click.option('-o', '--out_dir',
              type=click.Path(exists=True),
              required=True,
              help='Folder to save output file into')
@click.option('-s1', '--sample_1',
              required=True,
              help='ID of first sample')
@click.option('-s2', '--sample_2',
              required=True,
              help='ID of second sample')
@click.option('-t', '--taxonomic_level',
              required=False,
              default="family",
              help='Taxonomic level to generate pie charts from: ["phylum", "family", "genus", "species"]')
@click.option('-f', '--filtering',
              type=click.Path(exists=True),
              required=False,
              help='Filter dataset to a single group (i.e. Enterobacteriaceae)')
def cli(input_file, out_dir, sample_1, sample_2, taxonomic_level, filtering):
    # Quick validation
    if not os.path.isdir(out_dir):
        click.echo('ERROR: Provided parameter to [-o, --out_dir] is not a valid directory. Try again.')
        quit()

    create_paired_pie_wrapper(input_file, out_dir, sample_1, sample_2)
    click.echo('Created chart at {} successfully'.format(out_dir))

if __name__ == '__main__':
    cli()

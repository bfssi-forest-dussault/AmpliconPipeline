import os
import glob
import click
import pickle
import qiime2
import shutil
import random
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

from collections import OrderedDict


def extract_taxonomy(value):
    """
    :param value:
    :return:
    """
    if 'Unassigned;_' in value:
        return 'Unassigned'

    try:
        tax_string = value.split(TAXONOMIC_DICT[TAXONOMIC_LEVEL][1])[1]
        if tax_string == '':
            tax_string = value
    except:
        tax_string = value

    # Final cleanup
    if ';' in tax_string and '__' in tax_string:
        for i in reversed(tax_string.split(';')):
            if len(i) > 6:
                tax_string = i
                break

    return tax_string


def convert_to_percentages(df, cols):
    """
    :param df:
    :param cols:
    :return:
    """
    df[cols] = df[cols].div(df[cols].sum(axis=0), axis=1).multiply(100)
    return df


def get_column_pair(df, col1, col2):
    """
    :param df:
    :param col1:
    :param col2:
    :return:
    """
    # Filter columns
    df = df.filter([col1, col2], axis=1)

    # Sort
    df = df.sort_values(col1)
    return df


def prepare_df(filepath, index_col, filtering=None):
    """
    :param filepath:
    :param index_col:
    :return:
    """
    df = pd.read_csv(filepath, index_col=index_col)

    # Remove all extraneous metadata columns
    df = df.drop((x for x in df.columns.tolist()
                  if (x.startswith('D_0__') is False) and
                  (x.startswith('Unassigned;') is False)),
                 axis=1)

    # Remove columns that don't have target filtering keyword; e.g. remove everything that isn't Bacteroidales
    if filtering is not None:
        df = df.drop((x for x in df.columns.tolist() if filtering not in x), axis=1)

    # Transpose
    df = df.transpose()
    df = df.reset_index()

    # Create taxonomic basename column
    df[TAXONOMIC_LEVEL] = df['index'].map(extract_taxonomy)

    # Columns to target for conversion to percentage
    columns_to_target = [x for x in df.columns.tolist() if x not in ['index', TAXONOMIC_LEVEL]]

    # Convert
    df = convert_to_percentages(df, columns_to_target)

    return df


def fixed_df(filename, index='sample_annotation', filtering=None):
    """
    :param filename:
    :param index:
    :return:
    """
    df = prepare_df(filepath=filename, index_col=index, filtering=filtering)
    new_filename = filename.replace('.csv', '_temp.csv')

    # Stupid hack
    df.to_csv(new_filename, index=None)
    df = pd.read_csv(new_filename, index_col=TAXONOMIC_LEVEL).fillna('NA')

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
    """
    :param df:
    :param sampleid:
    :return:
    """
    labels = []
    values = []
    ordered_dict = df.to_dict(into=OrderedDict)[sampleid]
    ordered_dict = OrderedDict(sorted(ordered_dict.items(), key=lambda x: x[1], reverse=True))
    explode = [0 for x in range(len(ordered_dict))]

    # Set explodes
    explode[0] = 0.1

    try:
        explode[1] = 0.1
    except IndexError:
        pass

    try:
        explode[2] = 0.1
    except IndexError:
        pass

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
    """
    :param wedges:
    :param colordict:
    :return:
    """
    # Wedges
    for wedge in wedges:
        # wedge.set_color('black')
        try:
            wedge.set_facecolor(colordict[wedge.get_label()])
        except:
            wedge.set_facecolor(colordict[random.sample(list(colordict), 1)[0]])


def generate_pct_labels(labels, values):
    labels_values = zip(labels, values)
    pct_labels = []
    for label in labels_values:
        if label[0] != '':
            pct_labels.append(label[0] + '\n(%.2f' % label[1] + '%)')
        else:
            # pct_labels.append('')
            pass
    return pct_labels


def paired_pie_charts(values1, labels1, explode1, sample1, values2, labels2, explode2, sample2, out_dir):
    """
    :param values1:
    :param labels1:
    :param explode1:
    :param sample1:
    :param values2:
    :param labels2:
    :param explode2:
    :param sample2:
    :param out_dir:
    :return:
    """

    # Style setup
    plt.style.use('fivethirtyeight')

    # Consistent colouring across taxonomy. e.g. Listeria will always be red
    colordict = read_color_pickle()

    # Font size
    mpl.rcParams['font.size'] = 9.5

    # Setup figure canvas
    fig = plt.figure(figsize=(24, 16))
    fig.suptitle('16S Composition Comparison', fontsize=14, horizontalalignment='center', x=0.275, y=0.92)

    pct_labels1 = generate_pct_labels(labels1, values1)
    pct_labels2 = generate_pct_labels(labels2, values2)

    # Plot pie charts
    ax1 = plt.subplot2grid((3, 4), (0, 0))

    # wedges1 = ax1.pie(values1, labels=labels1, autopct=supress_autopct, startangle=90, explode=explode1, shadow=False)
    wedges1, labels1 = ax1.pie(values1, labels=labels1, startangle=90, explode=explode1, shadow=False)

    # Label fix
    for label, pct_label in zip(labels1, pct_labels1):
        label.set_text(pct_label)

    style_wedges(wedges=wedges1, colordict=colordict)
    # ax1.legend(labels=pct_labels1)

    ax1.axis('equal')
    plt.title(sample1)

    ax2 = plt.subplot2grid((3, 4), (0, 1))

    wedges2, labels2 = ax2.pie(values2, labels=labels2, startangle=90, explode=explode2, shadow=False)

    # Label fix
    for label, pct_label in zip(labels2, pct_labels2):
        label.set_text(pct_label)

    style_wedges(wedges=wedges2, colordict=colordict)
    # ax2.legend(labels=pct_labels2)

    ax2.axis('equal')
    plt.title(sample2)

    # Save
    outfile = os.path.join(out_dir, '{}_{}_{}_plot.png'.format(sample1, sample2, TAXONOMIC_LEVEL.capitalize()))
    plt.savefig(outfile, bbox_inches='tight')


def create_paired_pie_wrapper(filename, out_dir, sample1, sample2, filtering):
    """
    :param filename:
    :param out_dir:
    :param sample1:
    :param sample2:
    :return:
    """
    df = fixed_df(filename=filename, filtering=filtering)
    (values1, labels1, explode1) = prepare_plot(df, sample1)
    (values2, labels2, explode2) = prepare_plot(df, sample2)
    paired_pie_charts(values1, labels1, explode1, sample1,
                      values2, labels2, explode2, sample2,
                      out_dir)


def supress_autopct(pct):
    return ''


def my_autopct(pct):
    """
    :param pct:
    :return:
    """
    return (('%.2f' % pct) + '%') if pct > 2 else ''


def generate_color_pickle():
    """
    Generate a new color dictionary whenever necessary.
    Not all OTUs are covered - I should probably just pull from Silva...
    """
    phylums = glob.glob('/mnt/nas/Databases/GenBank/typestrains/Bacteria/*/*')
    classes = glob.glob('/mnt/nas/Databases/GenBank/typestrains/Bacteria/*/*/*')
    orders = glob.glob('/mnt/nas/Databases/GenBank/typestrains/Bacteria/*/*/*/*')
    families = glob.glob('/mnt/nas/Databases/GenBank/typestrains/Bacteria/*/*/*/*')
    genuses = glob.glob('/mnt/nas/Databases/GenBank/typestrains/Bacteria/*/*/*/*/*')

    mega_tax = []
    mega_tax.extend(phylums)
    mega_tax.extend(classes)
    mega_tax.extend(orders)
    mega_tax.extend(families)
    mega_tax.extend(genuses)

    filtered_mega_tax = []
    for thing in mega_tax:
        if not thing.endswith('.gz'):
            filtered_mega_tax.append(os.path.basename(thing))

    len(filtered_mega_tax)

    def get_spaced_colors(n):
        max_value = 16581375  # 255**3
        interval = int(max_value / n)
        colors = [hex(I)[2:].zfill(6) for I in range(0, max_value, interval)]

        return [((int(i[:2], 16)) / 255, (int(i[2:4], 16)) / 255, (int(i[4:], 16) / 255)) for i in colors]

    thing = get_spaced_colors(len(filtered_mega_tax))

    colordict = {}
    for l, c in zip(filtered_mega_tax, thing):
        colordict[l] = c

    # manual additions
    colordict['Hafnia-Obesumbacterium'] = 'green'
    colordict['Enterobacteriales'] = 'lightblue'

    import pickle
    pickle.dump(colordict, open("taxonomic_color_dictionary.pickle", "wb"))


def read_color_pickle():
    colordict = pickle.load(open("taxonomic_color_dictionary.pickle", "rb"))
    return colordict


def extract_viz_csv(input_path, out_dir):
    """
    :param input_path:
    :param out_dir:
    :return:
    """
    # Load visualization file
    try:
        qzv = load_visualization(input_path)
    except:
        print('Could not load .qzv file. Quitting.')
        return None

    # Create temporary directory to dump contents into
    temp_dir = os.path.join(os.path.dirname(out_dir), 'temporary_qiime2_extraction')

    # Outfile path
    out_file = os.path.join(out_dir, 'qiime2_data_extract.csv')

    try:
        os.mkdir(temp_dir)
    except:
        shutil.rmtree(temp_dir)
        os.mkdir(temp_dir)

    # Grab CSV
    qzv.export_data(temp_dir)
    taxonomic_csv_path = os.path.join(temp_dir, TAXONOMIC_DICT[TAXONOMIC_LEVEL][0]+'.csv')

    # Move file
    os.rename(taxonomic_csv_path, out_file)

    # Cleanup
    shutil.rmtree(temp_dir)

    return out_file


# TODO: Implement taxonomic_level and filter
@click.command()
@click.option('-i', '--input_file',
              type=click.Path(exists=True),
              required=True,
              help='CSV file exported from taxonomy_barplot visualization (*.qzv). '
                   'You can also just point to the *.qzv file, in which case the '
                   'taxonomy level specified will be exported. Defaults to family-level.')
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
              help='Taxonomic level to generate pie charts with. Defaults to "family". Options: '
                   '["kingdom", "phylum", "class", "order", "family", "genus", "species"]')
@click.option('-f', '--filtering',
              required=False,
              help='Filter dataset to a single group (e.g. Enterobacteriaceae)')
def cli(input_file, out_dir, sample_1, sample_2, taxonomic_level, filtering):
    generate_color_pickle()

    # Quick validation
    if not os.path.isdir(out_dir):
        click.echo('ERROR: Provided parameter to [-o, --out_dir] is not a valid directory. Try again.')
        quit()

    # Global variables. This is a hacky way of accomodating a few functions.
    global TAXONOMIC_LEVEL
    TAXONOMIC_LEVEL = taxonomic_level

    global TAXONOMIC_DICT
    TAXONOMIC_DICT = {
        'kingdom': ('level-1', 'D_0__'),
        'phylum': ('level-2', 'D_1__'),
        'class': ('level-3', 'D_2__'),
        'order': ('level-4', 'D_3__'),
        'family': ('level-5', 'D_4__'),
        'genus': ('level-6', 'D_5__'),
        'species': ('level-7', 'D_6__'),
    }


    # Input file handling
    if input_file.endswith('.csv'):
        create_paired_pie_wrapper(input_file, out_dir, sample_1, sample_2, filtering)
    elif input_file.endswith('.qzv'):
        input_file = extract_viz_csv(input_path=input_file, out_dir=out_dir)
        if input_file is None:
            quit()
        else:
            create_paired_pie_wrapper(input_file, out_dir, sample_1, sample_2, filtering)
    else:
        click.echo('ERROR: Invalid input_file provided. Please ensure file is .csv or .qzv.')
        quit()

    click.echo('Created chart at {} successfully'.format(out_dir))

if __name__ == '__main__':
    cli()

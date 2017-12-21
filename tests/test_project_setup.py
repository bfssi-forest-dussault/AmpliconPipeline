import os
import pytest
from project_setup import *

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0, parentdir)


def test_execute_command():
    (empty_test_out, empty_test_err) = execute_command('')
    assert (empty_test_out, empty_test_err) == ('','')

    (echo_test_out, echo_test_err) = execute_command('echo test')
    assert (echo_test_out, echo_test_err) == ('test\n', '')

def test_retrieve_fastqgz():
    assert len(retrieve_fastqgz('tests/sample_miseq')) == 4

def test_retrieve_unique_sampleids():
    fastq_list = retrieve_fastqgz('tests/sample_miseq')
    assert len(retrieve_unique_sampleids(fastq_list)) == 2

def test_get_readpair():
    fastq_list = retrieve_fastqgz('tests/sample_miseq')
    sample_id_list = retrieve_unique_sampleids(fastq_list)
    for sample_id in sample_id_list:
        assert len(get_readpair(sample_id, fastq_list)) == 2

def test_append_dummy_barcodes():
    pass

def test_get_sample_dictionary():
    test_dict = get_sample_dictionary('tests/sample_miseq')
    assert len(test_dict) == 2
    assert '2017-SEQ-1113' and '2017-SEQ-1114' in test_dict

def test_valid_olc_id():
    test_dict = get_sample_dictionary('tests/sample_miseq')
    for key, value in test_dict.items():
        assert valid_olc_id(key) is True


BootStrap: debootstrap
OSVersion: xenial
MirrorURL: http://us.archive.ubuntu.com/ubuntu/

%labels
    Maintainer Forest Dussault
    Version v0.1

%help
This is the AmpliconPipeline Singularity container.
https://github.com/forestdussault/AmpliconPipeline

%environment
    DEBIAN_FRONTEND=noninteractive
    PATH=/usr/sbin:$PATH
    PATH=/home/ubuntu/miniconda/bin:$PATH
    PATH=/home/ubuntu/AmpliconPipeline:$PATH
    LANG=C.UTF-8

%post
    # Install basic stuff
    sed -i 's/$/ universe/' /etc/apt/sources.list
    apt-get -y --force-yes install vim
    apt-get update -y -qq
    apt-get install -y python-dev
    apt-get install -y git
    apt-get install -y curl
    apt-get install -y wget
    apt-get install -y python3-pip
    apt-get install -y ttf-dejavu
    apt-get install -y nano

    # Miniconda setup
    useradd -ms /bin/bash/ ubuntu
    cd ~
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /home/ubuntu/miniconda.sh
    bash /home/ubuntu/miniconda.sh -b -p /home/ubuntu/miniconda

    # Debug...
    ls /home/ubuntu/miniconda/bin

    # Have to hard code this for now?
    /home/ubuntu/miniconda/bin/conda update conda install -y python=3 && /home/ubuntu/miniconda/bin/conda update conda

    # AmpliconPipeline setup
    git clone https://github.com/forestdussault/AmpliconPipeline.git
    cd AmpliconPipeline/
    /home/ubuntu/miniconda/bin/conda create --name AmpliconPipeline --file requirements.txt

    # Retrieve classifier for AmpliconPipeline
    mkdir classifiers/
    curl -L https://ndownloader.figshare.com/files/10970087 -o classifiers/99_V3V4_Silva_naive_bayes_classifier.qza

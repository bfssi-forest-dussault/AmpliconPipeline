# Dockerfile for AmpliconPipeline
FROM ubuntu:16.04

MAINTAINER Forest Dussault <forest.dussault@inspection.gc.ca>

ENV DEBIAN_FRONTEND noninteractive

# Building the image
# docker build -t "ampliconpipeline:v0.9"

# Install packages
RUN apt-get update -y -qq && apt-get install -y \
	python-dev \
	git \
	curl \
	wget \
	python3-pip \
	ttf-dejavu \
	nano

ENV PATH /usr/sbin:$PATH
RUN useradd -ms /bin/bash/ ubuntu
USER ubuntu

WORKDIR HOME
RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /home/ubuntu/miniconda.sh
RUN bash /home/ubuntu/miniconda.sh -b -p /home/ubuntu/miniconda
ENV PATH /home/ubuntu/miniconda/bin:$PATH
RUN echo $PATH
RUN conda install -y python=3 \
	    && conda update conda

# Upgrade pip
RUN pip3 install --upgrade pip

# Install AmpliconPipeline
WORKDIR /home/ubuntu/
ENV PATH /home/ubuntu/AmpliconPipeline:$PATH
RUN git clone https://github.com/forestdussault/AmpliconPipeline.git
WORKDIR /home/ubuntu/AmpliconPipeline
RUN conda create --name AmpliconPipeline --file requirements.txt

# Retrieve the classifier
RUN mkdir /home/ubuntu/AmpliconPipeline/classifiers
RUN curl -L https://ndownloader.figshare.com/files/10970087 -o classifiers/99_V3V4_Silva_naive_bayes_classifier.qza

# Set the language to use utf-8 encoding
ENV LANG C.UTF-8

CMD /bin/bash -c "source activate AmpliconPipeline"

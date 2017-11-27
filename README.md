# Relevant Search

Code and Examples for [Relevant Search](http://manning.com/turnbull) by [Doug Turnbull](http://github.com/softwaredoug) and [John Berryman](http://github.com/jnbrymn). Published by [Manning Publications](http://manning.com).

Relevant Search is all about leveraging Solr and Elasticsearch to build more intelligent search applications with intuitive results!

# How to run

## Install Python

Examples for this book are written in Python 2.7 and use iPython notebook. The first thing you'll need to do is install Python, pip (the Python package installer).

1. Install Python for your platform [here](https://www.python.org/downloads/). For Windows we recommend the [ActivePython](http://www.activestate.com/activepython) distribution.
2. Install pip, the Python installer, by simply running `easy_install pip`

## Install Elasticsearch

The examples expect Elasticsearch to be hosted at localhost:9200. So you'll need to install Elasticsearch to work with the examples. There's two ways to install Elasticsearch

### Recommended: Vagrant

Vagrant is a tool for installing and provisioning virtual machines locally for development purposes. If you've never used vagrant, you can follow the installation instructions [here](https://docs.vagrantup.com/v2/installation/). OpenSource Connections maintains a basic Elasticsearch vagrant box [here](https://github.com/o19s/elasticsearch-vagrant).

To use the vagrant box

1. Install vagrant
2. Clone the Elasticsearch vagrant box from Github locally

   ```
   git clone git@github.com:o19s/elasticsearch-vagrant.git
   ```
3. Provision the Vagrant box (this install Elasticsearch and turns the box on)

   ```
   cd elasticsearch-vagrant
   vagrant up --provision
   ```
4. Confirm Elasticsearch is running

  ```
  curl -XGET http://localhost:9200
  ```
  
  or visit this URL in your browser. 
  
  You should see JSON returned from the Elasticsearch instance. Something like:

   ```json
      {
        "name" : "Mary Zero",
        "cluster_name" : "elasticsearch",
        "version" : {
          "number" : "2.0.0-rc1",
          "build_hash" : "4757962b01a4d837af282f90df9e1fbdb68b524e",
          "build_timestamp" : "2015-10-01T10:06:08Z",
          "build_snapshot" : false,
          "lucene_version" : "5.2.1"
        },
        "tagline" : "You Know, for Search"
      }
   ```

5. When you're done working with examples, turn off the Vagrant box

  ```
  vagrant halt
  ```


### Locally on Your Machine

Follow [Elasticsearch's instructions](http://www.elastic.co/guide/en/elasticsearch/reference/1.5/_installation.html) to install Elasticsearch on your machine. 

## Running The Python Examples

The examples are written in Python 2.7 in [ipython notebooks](http://ipython.org/notebook.html) depending only on a few basic libraries. The only external library needed is the [requests](http://docs.python-requests.org/en/latest/) HTTP library. Some of the external APIs require API keys (for example TMDB, you can obtain one [here](https://www.themoviedb.org/faq/api)).

To run the IPython Notebook Examples

1. First ensure you have git, python 2.7 and pip installed and in your PATH

2. Then use the following commands to install the required dependencies
  ```
  git clone git@github.com:o19s/relevant-search-book.git
  cd relevant-search-book
  pip install requests
  pip install jupyter
  cd ipython/
  ```

5. Launch!

  ```ipython notebook```

6. Play!

Switch to your default browser where the Ipython examples are ready for you to experiment with. Keep in mind many examples are order dependent, so you can't just jump to an interesting listing and run it. Indexing commands with certain settings and what not need to be run. Be sure to run the prior ipython notebook commands too!

Happy Searching!


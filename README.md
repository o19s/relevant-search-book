# Relevant Search

Code and Examples for [Relevant Search](http://manning.com/turnbull) by [Doug Turnbull](http://github.com/softwaredoug) and [John Berryman](http://github.com/jnbrymn). Published by [Manning Publications](http://manning.com).

Relevant Search is all about leveraging Solr and Elasticsearch to build more intelligent search applications with intuitive results!

# How to run

## Installing Elasticsearch

The examples expect Elasticsearch to be at localhost:9200. You can use our [Vagrant box](https://github.com/o19s/elasticsearch-vagrant). This will provision Elasticsearch for you and port forward to localhost:9200. You can also follow [Elasticsearch's instructions](http://www.elastic.co/guide/en/elasticsearch/reference/1.5/_installation.html). 

## Running The Python Examples

The examples are written in Python 2.7 in [ipython notebooks](http://ipython.org/notebook.html) depending only on a few basic libraries. The only external library needed is the [requests](http://docs.python-requests.org/en/latest/) HTTP library. Some of the external APIs require API keys (for example TMDB, you can obtain one [here](https://www.themoviedb.org/faq/api)).

To run the IPython Notebook Examples

1. First ensure you have git, python 2.7 and pip installed and in your PATH

2. Obtain a TMDB API Key [here]((https://www.themoviedb.org/faq/api). 

4. Then use the following commands to install the required dependencies
```
git clone git@github.com:o19s/relevant-search-book.git
cd relevant-search-book
pip install requests
pip install ipython
cd ipython/
export TMDB_API_KEY=<...>
```

3. OPTIONAL Download tmdb json

For results consistent with the book, you can download [tmdb.json](https://s3.amazonaws.com/splainer.io/relevant-search/tmdb.json.tar.gz) and place it in the ipython folder. The link here points to a the TMDB data used to develop this book and should provide more consistent search results that the constantly updating TMDB database.

4. Launch!

```ipython notebook```

5. Play!

Switch to your default browser where the Ipython examples are ready for you to experiment with. Keep in mind many examples are order dependent, so you can't just jump to an interesting listing and run it. Be sure to run the prior ipython notebook commands too!

Happy Searching!

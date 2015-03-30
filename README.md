# Taming Search

Code and Examples for [Taming Search](http://manning.com/turnbull) by [Doug Turnbull](http://github.com/softwaredoug) and [John Berryman](http://github.com/jnbrymn).

# How to run

## Installing Elasticsearch

The examples expect Elasticsearch to be at localhost:9200. You can use our [Vagrant box](https://github.com/o19s/elasticsearch-vagrant). This will provision Elasticsearch for you and port forward to localhost:9200. You can also follow [Elasticsearch's instructions](http://www.elastic.co/guide/en/elasticsearch/reference/1.5/_installation.html). 

## Running The Python Examples

The examples are written in Python 2.7 and utilize a few basic libraries. The only external library needed is the [requests](http://docs.python-requests.org/en/latest/) HTTP library. Some of the external APIs require API keys (for example TMDB, you can obtain one [here](https://www.themoviedb.org/faq/api)).

We recommend running the examples with Ipython Notebook:

```
git@github.com:o19s/taming-search-book.git
cd taming-search-book
pip install requests
pip install ipython
cd ipython/
export TMDB_API_KEY=<...>
ipyton notebook
```
Then switch to your default browser where the Ipython examples are ready for you to experiment with.

Don't want to fuss with ipython notebook? Then just use the .py files in the root directory.

Happy Searching!

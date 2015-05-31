import os
import requests
import cPickle
import json
es_url = elasticSearchUrl = "http://es:9200"
tmdb_api_key = os.environ["TMDB_API_KEY"]
tmdb_api = requests.Session()
tmdb_api.params = {'api_key': tmdb_api_key}
tmdb = "tmdb"
movie_file = "movies.p"
numMoviesToGrab = 20000  # 20K max


def gather_docs():
    print "gathering documents from tmdb"
    movie_ids = []
    num_pages = numMoviesToGrab / 20

    for page in range(1, num_pages + 1):
        http_resp = tmdb_api.get('https://api.themoviedb.org/3/movie/popular',
                                 params={'page': page})  # (1)
        json_response = json.loads(http_resp.text)  # (2)
        movies = json_response['results']
        for movie in movies:
            movie_ids.append(movie['id'])
    print len(movie_ids)

    movie_dict = {}
    for movieId in movie_ids:
        http_resp = tmdb_api.get("https://api.themoviedb.org/3/movie/%s" % movieId)
        movie = json.loads(http_resp.text)
        movie_dict[movieId] = movie

    return movie_dict


def index_from_file(movie_file=movie_file, index_name=tmdb, settings=None, mapping=None):
    try:
        movie_dict = cPickle.load(open(movie_file, "rb"))
        index_docs(movie_dict, index_name, settings, mapping)

    except IOError:
        print "Couldn't find movies. Gathering from TMDB."
        movie_dict = gather_docs()
        cPickle.dump(movie_dict, open(movie_file, "wb"))
        index_docs()


def index_docs(docs, index_name=tmdb, settings=None, mapping=None):
    if settings is None:
        settings = {}
    if 'settings' not in settings:
        settings['settings'] = {}

    # We need to explicitely set number of shards to 1 to eliminate the impact of
    # distributed IDF on our small collection
    # See also "Relavance is Broken!"
    # http://www.elastic.co/guide/en/elasticsearch/guide/current/relevance-is-broken.html
    settings["settings"]["number_of_shards"] = 1

    # delete the index
    requests.delete(es_url + '/' + index_name)

    # create new index
    resp = requests.put(es_url + '/' + index_name, data=json.dumps(settings))
    print resp.status_code

    # Bulk index title & overview to the movie endpoint
    print "Indexing %i movies" % len(docs)
    if isinstance(docs, dict):
        iterator = docs.iteritems()
    elif isinstance(docs, (set, tuple, list)):
        iterator = enumerate(docs)
    else:
        raise Exception("must be a dict of id->doc or a list of docs")
    bulk_movies = ""
    for id, movie in iterator:
        add_cmd = {"index": {"_index": index_name, "_type": "movie", "_id": id}}
        es_doc = movie
        bulk_movies += json.dumps(add_cmd) + "\n" + json.dumps(es_doc) + "\n"
    resp = requests.post(elasticSearchUrl + "/_bulk", data=bulk_movies)
    if not resp.ok:
        print resp.text


def get_tmdb_url():
    resp = requests.get(es_url + '/' + tmdb)
    if not resp.ok:
        index_docs()
    return es_url + '/' + tmdb


def flatten(l):
    [item for sublist in l for item in sublist]


def simpler_explain(explain_json, depth=0):
    print explain_json['description']
    result = " " * (depth * 2) + "%s, %s\n" % (explain_json['value'], explain_json['description'])

    if 'details' in explain_json:
        for detail in explain_json['details']:
            result += simpler_explain(detail, depth=depth + 1)
    return result

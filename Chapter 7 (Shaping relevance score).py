from tqdm import tqdm
import json
import logging
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import click

SENTINEL_BEGIN = "SENTINEL_BEGIN"
SENTINEL_END = "SENTINEL_END"


def flatten(l):
    [item for sublist in l for item in sublist]


def simpler_explain(explain_json, depth=0):
    result = " " * (depth * 2) + "%s, %s\n" % (explain_json['value'], explain_json['description'])
    if 'details' in explain_json:
        for detail in explain_json['details']:
            result += explain_json(detail, depth=depth + 1)
    return result


def extract():
    f = open('tmdb.json')
    if f:
        return json.loads(f.read())
    return {}


def transform_movie_for_index(movie):
    movie["title_exact_match"] = f"{SENTINEL_BEGIN} {movie['title']} {SENTINEL_END}"
    movie["names_exact_match"] = []
    for person in movie["directors"] + movie["cast"]:
        movie["names_exact_match"].append(f"{SENTINEL_BEGIN} {person['name']} {SENTINEL_END}")
    return movie


def reindex(elastic_search: Elasticsearch, movie_dict={}, analysis_settings={}, mapping_settings={}):
    if elastic_search.indices.exists(index="tmdb"):
        elastic_search.indices.delete(index="tmdb")
    settings = {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "index": {
            "analysis": analysis_settings
        }
    }

    elastic_search.indices.create(index="tmdb", settings=settings, mappings=mapping_settings)

    logging.info("building...")
    movies_for_dump = []
    index = 1
    for movie_id, movie in tqdm(movie_dict.items()):
        doc = {
            "_index": "tmdb",
            '_id': str(index),
            '_source': transform_movie_for_index(movie)
        }
        index += 1
        movies_for_dump.append(doc)
    with open("f.txt", "w") as file:
        file.write(json.dumps(movies_for_dump))
    file.close()
    bulk(elastic_search, movies_for_dump)
    logging.info("indexing...")


def print_query_results(query_response, explain=False):
    print(f"Got {query_response['hits']['total']['value']} Hits:")
    num = 1
    for hit in query_response['hits']['hits']:
        print(f"""{num}: {hit['_source']['title']} score: {hit['_score']}""")
        num += 1
        # Uncomment to see explanation for each hit
        if "_explanation" in hit.keys() and explain:
            for detail in hit['_explanation']["details"]:
                print(json.dumps(detail["details"], indent=True))


def query_scoring_tiers(user_query):
    return {
        "bool": {
            "should": [
                {
                    "match_phrase": {
                        "title_exact_match": {
                            "query": f"{SENTINEL_BEGIN} {user_query} {SENTINEL_END}",
                            "boost": 1000
                        }
                    }
                },
                {
                    "multi_match": {
                        "query": user_query,
                        "fields": ["overview", "title", "directors.name", "cast.name"],
                        "type": "cross_fields"
                    }
                }
            ]
        }
    }

@click.command()
@click.option("--cert")
@click.option("--password")
def main(cert, password):
    movie_dict = extract()
    # Authenticate from the constructor
    es = Elasticsearch(
        "https://localhost:9200",
        ca_certs=cert,
        basic_auth=("elastic", password)
    )

    analysis_settings = {
        "analyzer": {
            "default": {
                "type": "english"
            },
            "english_bigrams": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "porter_stem",
                    "bigram_filter"
                ]
            }
        },
        "filter": {
            "bigram_filter": {
                "type": "shingle",
                "max_shingle_size": 2,
                "min_shingle_size": 2,
                "output_unigrams": "false"
            }
        }
    }

    mapping_settings = {
        "properties": {
            "people": {
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "bigrammed": {
                                "type": "text",
                                "analyzer": "english_bigrams"
                            }
                        }
                    }
                }
            },
            "cast": {
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "english",
                        "copy_to": "people.name",
                        "fields": {
                            "bigrammed": {
                                "type": "text",
                                "analyzer": "english_bigrams"
                            }
                        }
                    }
                }
            }
        }
    }

    reindex(elastic_search=es, movie_dict=movie_dict, analysis_settings=analysis_settings,
            mapping_settings=mapping_settings)

    user_query = "william shatner patrick steward"

    query = {
        "multi_match": {
            "query": user_query,
            "fields": ["overview", "title", "directors.name", "cast.name"],
            "type": "cross_fields"
        }
    }

    resp = es.search(index="tmdb", query=query, explain=True, size=5)
    print_query_results(resp, explain=False)

    query_math_phrase = {
        "bool": {
            "should": [
                {"multi_match": {
                    "query": user_query,
                    "fields": ["overview", "title", "directors.name", "cast.name"],
                    "type": "cross_fields"
                }},
                {"match_phrase": {
                    "title": {
                        "query": "star trek"
                    }
                }}
            ]
        }
    }

    resp = es.search(index="tmdb", query=query_math_phrase, explain=True, size=5)
    print_query_results(resp, explain=False)

    function_query = {
        "function_score": {
            "query": {
                "multi_match": {
                    "query": user_query,
                    "fields": ["overview", "title", "directors.name", "cast.name"],
                    "type": "cross_fields"
                }
            },
            "functions": [
                {
                    "weight": 2.5,
                    "filter": {
                        "match_phrase": {
                            "title": "star trek"
                        }
                    }
                }
            ]
        }
    }

    resp = es.search(index="tmdb", query=function_query, explain=True, size=5)
    print_query_results(resp, explain=False)

    query_exact_title_match = {
        "match_phrase": {
            "title_exact_match": {
                "query": f"{SENTINEL_BEGIN} star trek {SENTINEL_END}",
                "boost": 0.1
            }
        }
    }
    resp = es.search(index="tmdb", query=query_exact_title_match, explain=True, size=5)
    print_query_results(resp, explain=False)

    resp = es.search(index="tmdb", query=query_scoring_tiers("star trek"), explain=True, size=5)
    print_query_results(resp, explain=False)

    resp = es.search(index="tmdb", query=query_scoring_tiers("Good Will Hunting"), explain=True, size=5)
    print_query_results(resp, explain=False)


if __name__ == "__main__":
    main()

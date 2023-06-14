from tqdm import tqdm
import json
import logging
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


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
            '_source': movie
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


def main():
    movie_dict = extract()
    # Authenticate from the constructor
    es = Elasticsearch(
        "https://localhost:9200",
        ca_certs="/home/peczek/Programs/elasticsearch-8.7.1/config/certs/http_ca.crt",
        basic_auth=("elastic", "RXW*2QC=dceb-JR=vnEc")
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
            "cast": {
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
            }
        }
    }

    reindex(elastic_search=es, movie_dict=movie_dict, analysis_settings=analysis_settings,
            mapping_settings=mapping_settings)

    query = {
        "query_string": {
            "query": "start trek patrick stewart william shatner",
            "fields": ["title", "overview", "cast.name.bigrammed", "directors.name.bigrammed"]
        }
    }

    query_no_bigrammed = {
        "query_string": {
            "query": "start trek patrick stewart william shatner",
            "fields": ["title", "overview", "cast.name", "directors.name"]
        }
    }

    query_cast_boosted = {
        "query_string": {
            "query": "start trek patrick stewart william shatner",
            "fields": ["title", "overview", "cast.name^10", "directors.name"]
        }
    }

    resp = es.search(index="tmdb", query=query, explain=True, size=5)
    print_query_results(resp, explain=False)

    resp = es.search(index="tmdb", query=query_no_bigrammed, explain=True, size=5)
    print_query_results(resp, explain=False)

    resp = es.search(index="tmdb", query=query_cast_boosted, explain=True, size=5)
    print_query_results(resp, explain=False)


if __name__ == "__main__":
    main()

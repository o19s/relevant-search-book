from tqdm import tqdm
import json
import logging
from elasticsearch import Elasticsearch


def flatten(l):
    [item for sublist in l for item in sublist]


def simpler_explain(explain_json, depth=0):
    result = " " * (depth * 2) + "%s, %s\n" % (explain_json['value'], explain_json['description'])
    if 'details' in explain_json:
        for detail in explain_json['details']:
            result += explain_json(detail, depth=depth+1)
    return result


def extract():
    f = open('tmdb.json')
    if f:
        return json.loads(f.read())
    return {}


def reindex(elastic_search: Elasticsearch, movie_dict={}):

    logging.info("building...")
    for movie_id, movie in tqdm(movie_dict.items()):
        doc = {
            'movie_id': movie["id"],
            'movie_title': movie["title"],
            'movie_overview': movie["overview"]
        }
        elastic_search.index(index="tmdb", id=movie_id, document=doc)

    logging.info("indexing...")


def print_query_results(query_response, explain=False):
    print(f"Got {query_response['hits']['total']['value']} Hits:")
    num = 1
    for hit in query_response['hits']['hits']:
        print(f"""{num}: {hit['_source']['movie_title']} score: {hit['_score']}""")
        num+=1
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

    mapping_settings = {
        "properties": {
            "movie_title": {
                "type": "text",
                "analyzer": "english"
            },
            "movie_overview": {
                "type": "text",
                "analyzer": "english"
            }
        }
    }

    settings = {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }

    # es.indices.delete(index="tmdb")
    if not es.indices.exists(index="tmdb"):
        es.indices.create(index="tmdb", mappings=mapping_settings, settings=settings)
        reindex(elastic_search=es, movie_dict=movie_dict)

    query_string = "basketball with cartoon aliens"

    query = {
        "multi_match": {
            "query": query_string,
            "fields": ["movie_title^10", "movie_overview"]
        }
    }

    query_lower_title = {
        "multi_match": {
            "query": query_string,
            "fields": ["movie_title^0.1", "movie_overview"]
        }
    }
    print("Normal Query")
    resp = es.search(index="tmdb", query=query, from_=30, explain=True)
    print_query_results(resp)
    print()
    print("Query with title smaller")
    resp = es.search(index="tmdb", query=query_lower_title, explain=True)
    print_query_results(resp, explain=False)


if __name__ == "__main__":
    main()

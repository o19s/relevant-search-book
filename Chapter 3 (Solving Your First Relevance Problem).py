
## Boilerplate Setup

# In[2]:

import requests
import json
import os

# you'll need to have an API key for TMDB
# to run these examples,
# run export TMDB_API_KEY=<YourAPIKey>
tmdb_api_key = os.environ["TMDB_API_KEY"]

# Setup tmdb as its own session, caching requests
# (we only want to cache tmdb, not elasticsearch)
# Get your TMDB API key from
#  https://www.themoviedb.org/documentation/api
# then in shell do export TMDB_API_KEY=<Your Key>
tmdb_api = requests.Session()
tmdb_api.params={'api_key': tmdb_api_key}

# Optional, enable client-side caching for TMDB
# Requires: https://httpcache.readthedocs.org/en/latest/
#from httpcache import CachingHTTPAdapter
#tmdb_api.mount('https://', CachingHTTPAdapter())
#tmdb_api.mount('http://', CachingHTTPAdapter())

# Some utilities for flattening the explain into something a bit more
# readable. Pass Explain JSON, get something readable (ironically this is what Solr's default output is :-p)
def flatten(l):
    [item for sublist in l for item in sublist]

def simplerExplain(explainJson, depth=0):
    result = " " * (depth * 2) + "%s, %s\n" % (explainJson['value'], explainJson['description'])
    #print json.dumps(explainJson, indent=True)
    if 'details' in explainJson:
        for detail in explainJson['details']:
            result += simplerExplain(detail, depth=depth+1)
    return result


## 3.2.2 Indexing TMDB Movies

# In[3]:

movieIds = [];
numMoviesToGrab = 10000
numPages = numMoviesToGrab / 20

for page in range(1, numPages + 1):
    httpResp = tmdb_api.get('https://api.themoviedb.org/3/movie/top_rated', params={'page': page})  #(1)
    jsonResponse = json.loads(httpResp.text) #(2)
    movies = jsonResponse['results']
    for movie in movies:
        if (movie['id'] not in [9549]):
            movieIds.append(movie['id'])
print len(movieIds)


# Out[3]:

#     2925
# 

# In[4]:

movieDict = {}
for movieId in movieIds:
    httpResp = tmdb_api.get("https://api.themoviedb.org/3/movie/%s" % movieId)
    movie = json.loads(httpResp.text)
    movieDict[movieId] = movie


# In[7]:

# Destroy any existing index (equiv to SQL "drop table")
resp = requests.delete("http://localhost:9200/tmdb")
print resp.status_code

# Create the index with explicit settings
# We need to explicitely set number of shards to 1 to eliminate the impact of 
# distributed IDF on our small collection
# See also "Relavance is Broken!"
# http://www.elastic.co/guide/en/elasticsearch/guide/current/relevance-is-broken.html
settings = {
    "settings": {"number_of_shards": 1}
}
resp = requests.put("http://localhost:9200/tmdb", data=json.dumps(settings))
print resp.status_code

# Bulk index title & overview to the movie endpoint
print "Indexing %i movies" % len(movieDict.keys())
bulkMovies = ""
for id, movie in movieDict.iteritems():
    addCmd = {"index": {"_index": "tmdb", "_type": "movie", "_id": movie["id"]}}
    esDoc  = {"title": movie['title'], 'overview': movie['overview'], 'tagline': movie['tagline']}
    bulkMovies += json.dumps(addCmd) + "\n" + json.dumps(esDoc) + "\n"
requests.post("http://localhost:9200/_bulk", data=bulkMovies)


# Out[7]:

#     200
#     200
#     Indexing 2919 movies
# 

#     <Response [200]>

## 3.2.3 Basic Searching

# In[9]:

usersSearch = 'basketball with cartoon aliens'
search = {
    'query': {
        'multi_match': { 
            'query': usersSearch,  #User's query
            'fields': ['title^10', 'overview'],
        }
    },
    'size': '100',
    'explain': True
}

httpResp = requests.get('http://localhost:9200/tmdb/movie/_search', data=json.dumps(search))
searchHits = json.loads(httpResp.text)['hits']
print "Num\tRelevance Score\t\tMovie Title\t\tOverview"
for idx, hit in enumerate(searchHits['hits']):
        print "%s\t%s\t\t%s\t\t%s" % (idx + 1, hit['_score'], hit['_source']['title'], len(hit['_source']['overview']))


# Out[9]:

#     Num	Relevance Score		Movie Title		Overview
#     1	0.8456088		Aliens		357
#     2	0.56193966		The Basketball Diaries		131
#     3	0.5285055		Cowboys & Aliens		367
#     4	0.4228044		Aliens vs Predator: Requiem		481
#     5	0.4228044		Aliens in the Attic		617
#     6	0.4228044		Monsters vs Aliens		333
#     7	0.26435968		Dances with Wolves		241
#     8	0.26435968		Interview with the Vampire		113
#     9	0.26435968		From Russia With Love		391
#     10	0.26435968		Gone with the Wind		163
#     11	0.26435968		Friends with Benefits		178
#     12	0.26435968		Just Go With It		328
#     13	0.26435968		Fire with Fire		165
#     14	0.26435968		My Week with Marilyn		534
#     15	0.26435968		From Paris with Love		239
#     16	0.26435968		Trouble with the Curve		245
#     17	0.26435968		Friends with Kids		214
#     18	0.26435968		To Rome with Love		305
#     19	0.23131472		Die Hard: With a Vengeance		382
#     20	0.23131472		Girl with a Pearl Earring		364
#     21	0.23131472		Fun with Dick and Jane		373
#     22	0.19826975		The Life Aquatic With Steve Zissou		342
#     23	0.19826975		The Girl with the Dragon Tattoo		423
#     24	0.19826975		Twin Peaks: Fire Walk with Me		498
#     25	0.19826975		You Don't Mess With the Zohan		269
#     26	0.19826975		Cloudy with a Chance of Meatballs 2		533
#     27	0.19826975		The Man with the Golden Gun		228
#     28	0.19826975		Cloudy with a Chance of Meatballs		342
#     29	0.19826975		The Pirates! In an Adventure with Scientists!		840
#     30	0.19826975		The Girl with the Dragon Tattoo		391
#     31	0.19826975		The Man with the Iron Fists		145
#     32	0.19826975		The Girl Who Played with Fire		372
#     33	0.031029418		Meet Dave		191
#     34	0.026974695		Speed Racer		280
#     35	0.022064768		Semi-Pro		740
#     36	0.021042004		Bedazzled		326
#     37	0.018656164		District 9		328
#     38	0.01800988		The Watch		313
#     39	0.01800988		Alien: Resurrection		260
#     40	0.017046522		Space Jam		119
#     41	0.015758647		They Live		427
#     42	0.014611304		Grown Ups		138
#     43	0.013992123		Men in Black 3		572
#     44	0.012707215		The Flintstones		280
#     45	0.012176087		White Men Can't Jump		221
#     46	0.012176087		Coach Carter		171
#     47	0.01028101		Galaxy Quest		230
#     48	0.008523261		High School Musical		435
#     49	0.008224808		AVP: Alien vs. Predator		344
#     50	0.008224808		Pitch Black		361
#     51	0.008224808		Batteries Not Included		249
#     52	0.0071967067		Battlefield Earth		394
#     53	0.0071967067		Dude, Where’s My Car?		398
#     54	0.0019307307		Sex Drive		101
#     55	0.0016890374		Dark City		186
#     56	0.001654912		Silver Linings Playbook		141
#     57	0.001654912		Strangers on a Train		157
#     58	0.001654912		Nim's Island		135
#     59	0.001654912		The Guard		156
#     60	0.001654912		[REC]²		167
#     61	0.001654912		Cinema Paradiso		159
#     62	0.001654912		Wild Card		145
#     63	0.001654912		Bride of Chucky		130
#     64	0.001654912		Safe Haven		157
#     65	0.001654912		Young Adult		123
#     66	0.001654912		Odd Thomas		143
#     67	0.001560266		Adam's Apples		97
#     68	0.001560266		Teenage Mutant Ninja Turtles		84
#     69	0.001560266		Crash		109
#     70	0.001560266		Shallow Hal		81
#     71	0.001560266		Becoming Jane		88
#     72	0.001560266		Bandits		62
#     73	0.001560266		Fantasia 2000		90
#     74	0.001560266		The Curious Case of Benjamin Button		95
#     75	0.001560266		Desperado		60
#     76	0.0013790933		8½		195
#     77	0.0013790933		Charlie's Angels: Full Throttle		236
#     78	0.0013790933		Ghost World		210
#     79	0.0013790933		Just Friends		204
#     80	0.0013790933		Stuart Little		219
#     81	0.0013790933		Fantastic Mr. Fox		201
#     82	0.0013790933		Lady and the Tramp		210
#     83	0.0013790933		Outlander		213
#     84	0.0013790933		Trance		242
#     85	0.0013790933		Step Up Revolution		193
#     86	0.0013790933		Robin Hood		239
#     87	0.0013790933		The Graduate		249
#     88	0.0013790933		My Big Fat Greek Wedding		162
#     89	0.0013790933		Stoker		239
#     90	0.0013790933		Howl's Moving Castle		218
#     91	0.0013790933		Vicky Cristina Barcelona		188
#     92	0.0013790933		Mesrine: Killer Instinct		254
#     93	0.0013790933		27 Dresses		169
#     94	0.0013790933		Rust and Bone		224
#     95	0.0013790933		Submarine		241
#     96	0.0013790933		The Spiderwick Chronicles		220
#     97	0.0013652327		Sin City: A Dame to Kill For		100
#     98	0.0013652327		Spider-Man		122
#     99	0.0013652327		The French Connection		102
#     100	0.0013652327		Frida		427
# 

## 2.3.1 Query Validation API

# In[10]:

search = {
   'query': {
        'multi_match': { 
            'query': usersSearch,  #User's query
            'fields': ['title^10', 'overview']
        }
    }
}
httpResp = requests.get('http://localhost:9200' + 
			    '/tmdb/movie/_validate/query?explain',
			     data=json.dumps(search))
print json.loads(httpResp.text)


# Out[10]:

#     {u'valid': True, u'explanations': [{u'index': u'tmdb', u'explanation': u'filtered((((title:basketball title:with title:cartoon title:aliens)^10.0) | (overview:basketball overview:with overview:cartoon overview:aliens)))->cache(_type:movie)', u'valid': True}], u'_shards': {u'successful': 1, u'failed': 0, u'total': 1}}
# 

## 2.3.3 Debugging Analysis

# In[15]:

# Inner Layer of the Onion -- Why did the search engine consider these movies matches? Two sides to this
# (1) What tokens are placed in the search engine?
# (2) What did the search engine attempt to match exactly?

# Explain of what's happening when we construct these terms

#resp = requests.get(elasticSearchUrl + "/tmdb/_mapping/movie/field/title?format=yaml'
resp = requests.get('http://localhost:9200/tmdb/_analyze?field=title&format=yaml', 
                    data="Fire with Fire")
print resp.text


# Out[15]:

#     ---
#     tokens:
#     - token: "fire"
#       start_offset: 0
#       end_offset: 4
#       type: "<ALPHANUM>"
#       position: 1
#     - token: "fire"
#       start_offset: 10
#       end_offset: 14
#       type: "<ALPHANUM>"
#       position: 3
#     
# 

## 2.3.5 -- Solving The Matching Problem

# In[18]:

from time import sleep

# DELETE AND RECREATE THE INDEX WITH ENGLISH ANALYZERS
requests.delete('http://localhost:9200/tmdb')

settings = {
    'settings': {
        "number_of_shards": 1,
    },
    'mappings': {
            'movie': {
                'properties': {
                    'title': {
                        'type': 'string',
                        'analyzer': 'english'
                    },
                    'overview': {
                        'type': 'string',
                        'analyzer': 'english'
                    }
                }
                
            }
       }
    
}

resp = requests.put('http://localhost:9200/tmdb/', data=json.dumps(settings))
print resp.text
sleep(1)

# Inspecting the mappings
resp = requests.get('http://localhost:9200/tmdb/_mappings?format=yaml')
print resp.text

# Reanalyze the string
resp = requests.get('http://localhost:9200/tmdb/_analyze?field=title&format=yaml', 
                    data="Fire with Fire")
print resp.text


# Reindex
resp = requests.post('http://localhost:9200/_bulk', data=bulkMovies)
resp = requests.get('http://localhost:9200/tmdb/_refresh')
print resp.text

sleep(1)

# Search again
search = {
    'query': {
        'multi_match': { 
            'query': usersSearch,  #User's query
            'fields': ['title^10', 'overview'],
        }
    },
    'size': '100',
    'explain': True
}
httpResp = requests.get('http://localhost:9200/tmdb/movie/_search', data=json.dumps(search))
searchHits = json.loads(httpResp.text)['hits']

print "Num\tRelevance Score\t\tMovie Title\t\tOverview"
for idx, hit in enumerate(searchHits['hits']):
        print "%s\t%s\t\t%s\t\t%s" % (idx + 1, hit['_score'], hit['_source']['title'], len(hit['_source']['overview']))


# Out[18]:

#     {"acknowledged":true}
#     ---
#     tmdb:
#       mappings:
#         movie:
#           properties:
#             overview:
#               type: "string"
#               analyzer: "english"
#             title:
#               type: "string"
#               analyzer: "english"
#     
#     ---
#     tokens:
#     - token: "fire"
#       start_offset: 0
#       end_offset: 4
#       type: "<ALPHANUM>"
#       position: 1
#     - token: "fire"
#       start_offset: 10
#       end_offset: 14
#       type: "<ALPHANUM>"
#       position: 3
#     
#     {"_shards":{"total":2,"successful":1,"failed":0}}
#     Num	Relevance Score		Movie Title		Overview
#     1	1.0671602		Alien		420
#     2	1.0671602		Aliens		357
#     3	1.0671602		Alien³		380
#     4	1.0273007		The Basketball Diaries		131
#     5	0.66697514		Cowboys & Aliens		367
#     6	0.66697514		Aliens in the Attic		617
#     7	0.66697514		Alien: Resurrection		260
#     8	0.5335801		Aliens vs Predator: Requiem		481
#     9	0.5335801		AVP: Alien vs. Predator		344
#     10	0.5335801		Monsters vs Aliens		333
#     11	0.083611175		Space Jam		119
#     12	0.024930652		Grown Ups		138
#     13	0.023230484		The Flintstones		280
#     14	0.023230484		Speed Racer		280
#     15	0.02136913		White Men Can't Jump		221
#     16	0.02136913		Coach Carter		171
#     17	0.01850621		Semi-Pro		740
#     18	0.016641766		The Thing		125
#     19	0.014246087		High School Musical		435
#     20	0.014246087		Bedazzled		326
#     21	0.014121006		Meet Dave		191
#     22	0.013313412		Escape from Planet Earth		127
#     23	0.013313412		The Darkest Hour		98
#     24	0.013313412		Invasion of the Body Snatchers		114
#     25	0.013313412		Slither		111
#     26	0.011767505		District 9		328
#     27	0.011649235		Avatar		175
#     28	0.011649235		The Last Starfighter		147
#     29	0.010088533		The X Files		708
#     30	0.009985059		Napoleon Dynamite		184
#     31	0.009985059		The Day the Earth Stood Still		183
#     32	0.009985059		Galaxy Quest		230
#     33	0.009985059		Outlander		213
#     34	0.009985059		Scary Movie 3		216
#     35	0.009985059		Titan A.E.		179
#     36	0.009985059		The Hitchhiker's Guide to the Galaxy		222
#     37	0.009414004		Star Trek IV: The Voyage Home		573
#     38	0.009414004		Independence Day		393
#     39	0.009414004		Ghosts of Mars		539
#     40	0.009414004		Dude, Where’s My Car?		398
#     41	0.009414004		Edge of Tomorrow		371
#     42	0.008320883		Contact		252
#     43	0.008320883		Star Trek: Insurrection		277
#     44	0.008320883		Predators		321
#     45	0.008320883		Mars Attacks!		289
#     46	0.008320883		Pitch Black		361
#     47	0.008320883		Batteries Not Included		249
#     48	0.008320883		Lifted		320
#     49	0.008320883		Scary Movie 4		224
#     50	0.008320883		Justice League: War		272
#     51	0.008320883		The Watch		313
#     52	0.008320883		Species		327
#     53	0.008320883		The Host		239
#     54	0.008320883		Under the Skin		249
#     55	0.008237254		Attack the Block		533
#     56	0.008237254		Battleship		606
#     57	0.006656706		Predator		465
#     58	0.006656706		Predator 2		407
#     59	0.006656706		Men in Black		503
#     60	0.006656706		They Live		427
#     61	0.006656706		Battlefield Earth		394
#     62	0.006656706		The Faculty		441
#     63	0.006656706		The Day the Earth Stood Still		350
#     64	0.006656706		Short Circuit		349
#     65	0.006656706		Monsters		479
#     66	0.006656706		Lilo & Stitch		305
#     67	0.006656706		Spider-Man 3		357
#     68	0.006656706		Doom		459
#     69	0.006656706		Halo 4: Forward Unto Dawn		580
#     70	0.006656706		The Invasion		451
#     71	0.006656706		Riddick		471
#     72	0.006656706		Dreamcatcher		413
#     73	0.006656706		Spring Breakers		536
#     74	0.006656706		Paul		431
#     75	0.0058246176		Men in Black II		634
#     76	0.0058246176		Men in Black 3		572
#     77	0.0058246176		Pride		673
#     78	0.0058246176		Mars Needs Moms		537
#     79	0.0058246176		There Will Be Blood		633
#     80	0.0049925293		Stalker		755
#     81	0.0049925293		Wreck-It Ralph		658
# 

## 2.4.1	Decomposing Relevance Score With Lucene’s Explain

# In[12]:

search['explain'] = True
httpResp = requests.get(elasticSearchUrl + '/tmdb/movie/_search', data=json.dumps(search))
jsonResp = json.loads(httpResp.text)
print json.dumps(jsonResp['hits']['hits'][0]['_explanation'], indent=True)
print "Explain for %s" % jsonResp['hits']['hits'][0]['_source']['title']
print simplerExplain(jsonResp['hits']['hits'][0]['_explanation'])
print "Explain for %s" % jsonResp['hits']['hits'][1]['_source']['title']
print simplerExplain(jsonResp['hits']['hits'][1]['_explanation'])
print "Explain for %s" % jsonResp['hits']['hits'][2]['_source']['title']
print simplerExplain(jsonResp['hits']['hits'][2]['_explanation'])
print "Explain for %s" % jsonResp['hits']['hits'][3]['_source']['title']
print simplerExplain(jsonResp['hits']['hits'][3]['_explanation'])
print "Explain for %s" % jsonResp['hits']['hits'][10]['_source']['title']
print simplerExplain(jsonResp['hits']['hits'][10]['_explanation'])


# Out[12]:

#     {
#      "description": "max of:", 
#      "value": 1.0643067, 
#      "details": [
#       {
#        "description": "product of:", 
#        "value": 1.0643067, 
#        "details": [
#         {
#          "description": "sum of:", 
#          "value": 3.19292, 
#          "details": [
#           {
#            "description": "weight(title:alien in 223) [PerFieldSimilarity], result of:", 
#            "value": 3.19292, 
#            "details": [
#             {
#              "description": "score(doc=223,freq=1.0 = termFreq=1.0\n), product of:", 
#              "value": 3.19292, 
#              "details": [
#               {
#                "description": "queryWeight, product of:", 
#                "value": 0.4793294, 
#                "details": [
#                 {
#                  "description": "idf(docFreq=9, maxDocs=2875)", 
#                  "value": 6.661223
#                 }, 
#                 {
#                  "description": "queryNorm", 
#                  "value": 0.07195817
#                 }
#                ]
#               }, 
#               {
#                "description": "fieldWeight in 223, product of:", 
#                "value": 6.661223, 
#                "details": [
#                 {
#                  "description": "tf(freq=1.0), with freq of:", 
#                  "value": 1.0, 
#                  "details": [
#                   {
#                    "description": "termFreq=1.0", 
#                    "value": 1.0
#                   }
#                  ]
#                 }, 
#                 {
#                  "description": "idf(docFreq=9, maxDocs=2875)", 
#                  "value": 6.661223
#                 }, 
#                 {
#                  "description": "fieldNorm(doc=223)", 
#                  "value": 1.0
#                 }
#                ]
#               }
#              ]
#             }
#            ]
#           }
#          ]
#         }, 
#         {
#          "description": "coord(1/3)", 
#          "value": 0.33333334
#         }
#        ]
#       }, 
#       {
#        "description": "product of:", 
#        "value": 0.00662633, 
#        "details": [
#         {
#          "description": "sum of:", 
#          "value": 0.01987899, 
#          "details": [
#           {
#            "description": "weight(overview:alien in 223) [PerFieldSimilarity], result of:", 
#            "value": 0.01987899, 
#            "details": [
#             {
#              "description": "score(doc=223,freq=1.0 = termFreq=1.0\n), product of:", 
#              "value": 0.01987899, 
#              "details": [
#               {
#                "description": "queryWeight, product of:", 
#                "value": 0.03382846, 
#                "details": [
#                 {
#                  "description": "idf(docFreq=70, maxDocs=2875)", 
#                  "value": 4.701128
#                 }, 
#                 {
#                  "description": "queryNorm", 
#                  "value": 0.0071958173
#                 }
#                ]
#               }, 
#               {
#                "description": "fieldWeight in 223, product of:", 
#                "value": 0.587641, 
#                "details": [
#                 {
#                  "description": "tf(freq=1.0), with freq of:", 
#                  "value": 1.0, 
#                  "details": [
#                   {
#                    "description": "termFreq=1.0", 
#                    "value": 1.0
#                   }
#                  ]
#                 }, 
#                 {
#                  "description": "idf(docFreq=70, maxDocs=2875)", 
#                  "value": 4.701128
#                 }, 
#                 {
#                  "description": "fieldNorm(doc=223)", 
#                  "value": 0.125
#                 }
#                ]
#               }
#              ]
#             }
#            ]
#           }
#          ]
#         }, 
#         {
#          "description": "coord(1/3)", 
#          "value": 0.33333334
#         }
#        ]
#       }
#      ]
#     }
#     Explain for Alien
#     1.0643067, max of:
#       1.0643067, product of:
#         3.19292, sum of:
#           3.19292, weight(title:alien in 223) [PerFieldSimilarity], result of:
#             3.19292, score(doc=223,freq=1.0 = termFreq=1.0
#     ), product of:
#               0.4793294, queryWeight, product of:
#                 6.661223, idf(docFreq=9, maxDocs=2875)
#                 0.07195817, queryNorm
#               6.661223, fieldWeight in 223, product of:
#                 1.0, tf(freq=1.0), with freq of:
#                   1.0, termFreq=1.0
#                 6.661223, idf(docFreq=9, maxDocs=2875)
#                 1.0, fieldNorm(doc=223)
#         0.33333334, coord(1/3)
#       0.00662633, product of:
#         0.01987899, sum of:
#           0.01987899, weight(overview:alien in 223) [PerFieldSimilarity], result of:
#             0.01987899, score(doc=223,freq=1.0 = termFreq=1.0
#     ), product of:
#               0.03382846, queryWeight, product of:
#                 4.701128, idf(docFreq=70, maxDocs=2875)
#                 0.0071958173, queryNorm
#               0.587641, fieldWeight in 223, product of:
#                 1.0, tf(freq=1.0), with freq of:
#                   1.0, termFreq=1.0
#                 4.701128, idf(docFreq=70, maxDocs=2875)
#                 0.125, fieldNorm(doc=223)
#         0.33333334, coord(1/3)
#     
#     Explain for Aliens
#     1.0643067, max of:
#       1.0643067, product of:
#         3.19292, sum of:
#           3.19292, weight(title:alien in 435) [PerFieldSimilarity], result of:
#             3.19292, score(doc=435,freq=1.0 = termFreq=1.0
#     ), product of:
#               0.4793294, queryWeight, product of:
#                 6.661223, idf(docFreq=9, maxDocs=2875)
#                 0.07195817, queryNorm
#               6.661223, fieldWeight in 435, product of:
#                 1.0, tf(freq=1.0), with freq of:
#                   1.0, termFreq=1.0
#                 6.661223, idf(docFreq=9, maxDocs=2875)
#                 1.0, fieldNorm(doc=435)
#         0.33333334, coord(1/3)
#       0.008282913, product of:
#         0.024848737, sum of:
#           0.024848737, weight(overview:alien in 435) [PerFieldSimilarity], result of:
#             0.024848737, score(doc=435,freq=1.0 = termFreq=1.0
#     ), product of:
#               0.03382846, queryWeight, product of:
#                 4.701128, idf(docFreq=70, maxDocs=2875)
#                 0.0071958173, queryNorm
#               0.73455125, fieldWeight in 435, product of:
#                 1.0, tf(freq=1.0), with freq of:
#                   1.0, termFreq=1.0
#                 4.701128, idf(docFreq=70, maxDocs=2875)
#                 0.15625, fieldNorm(doc=435)
#         0.33333334, coord(1/3)
#     
#     Explain for Alien³
#     1.0643067, max of:
#       1.0643067, product of:
#         3.19292, sum of:
#           3.19292, weight(title:alien in 2855) [PerFieldSimilarity], result of:
#             3.19292, score(doc=2855,freq=1.0 = termFreq=1.0
#     ), product of:
#               0.4793294, queryWeight, product of:
#                 6.661223, idf(docFreq=9, maxDocs=2875)
#                 0.07195817, queryNorm
#               6.661223, fieldWeight in 2855, product of:
#                 1.0, tf(freq=1.0), with freq of:
#                   1.0, termFreq=1.0
#                 6.661223, idf(docFreq=9, maxDocs=2875)
#                 1.0, fieldNorm(doc=2855)
#         0.33333334, coord(1/3)
#       0.00662633, product of:
#         0.01987899, sum of:
#           0.01987899, weight(overview:alien in 2855) [PerFieldSimilarity], result of:
#             0.01987899, score(doc=2855,freq=1.0 = termFreq=1.0
#     ), product of:
#               0.03382846, queryWeight, product of:
#                 4.701128, idf(docFreq=70, maxDocs=2875)
#                 0.0071958173, queryNorm
#               0.587641, fieldWeight in 2855, product of:
#                 1.0, tf(freq=1.0), with freq of:
#                   1.0, termFreq=1.0
#                 4.701128, idf(docFreq=70, maxDocs=2875)
#                 0.125, fieldNorm(doc=2855)
#         0.33333334, coord(1/3)
#     
#     Explain for The Basketball Diaries
#     1.0254613, max of:
#       1.0254613, product of:
#         3.0763838, sum of:
#           3.0763838, weight(title:basketbal in 1278) [PerFieldSimilarity], result of:
#             3.0763838, score(doc=1278,freq=1.0 = termFreq=1.0
#     ), product of:
#               0.5951416, queryWeight, product of:
#                 8.27066, idf(docFreq=1, maxDocs=2875)
#                 0.07195817, queryNorm
#               5.1691628, fieldWeight in 1278, product of:
#                 1.0, tf(freq=1.0), with freq of:
#                   1.0, termFreq=1.0
#                 8.27066, idf(docFreq=1, maxDocs=2875)
#                 0.625, fieldNorm(doc=1278)
#         0.33333334, coord(1/3)
#     
#     Explain for Space Jam
#     0.08334568, max of:
#       0.08334568, product of:
#         0.12501852, sum of:
#           0.08526054, weight(overview:basketbal in 1289) [PerFieldSimilarity], result of:
#             0.08526054, score(doc=1289,freq=1.0 = termFreq=1.0
#     ), product of:
#               0.049538642, queryWeight, product of:
#                 6.8843665, idf(docFreq=7, maxDocs=2875)
#                 0.0071958173, queryNorm
#               1.7210916, fieldWeight in 1289, product of:
#                 1.0, tf(freq=1.0), with freq of:
#                   1.0, termFreq=1.0
#                 6.8843665, idf(docFreq=7, maxDocs=2875)
#                 0.25, fieldNorm(doc=1289)
#           0.03975798, weight(overview:alien in 1289) [PerFieldSimilarity], result of:
#             0.03975798, score(doc=1289,freq=1.0 = termFreq=1.0
#     ), product of:
#               0.03382846, queryWeight, product of:
#                 4.701128, idf(docFreq=70, maxDocs=2875)
#                 0.0071958173, queryNorm
#               1.175282, fieldWeight in 1289, product of:
#                 1.0, tf(freq=1.0), with freq of:
#                   1.0, termFreq=1.0
#                 4.701128, idf(docFreq=70, maxDocs=2875)
#                 0.25, fieldNorm(doc=1289)
#         0.6666667, coord(2/3)
#     
# 

## 2.4.4	Fixing Space Jam vs Alien Ranking

# In[20]:

# Search with saner boosts
search = {
    'query': {
        'multi_match': { 
            'query': usersSearch,  #User's query
            'fields': ['title^0.1', 'overview'],
        }
    },
    'size': '100',
    'explain': True
}
httpResp = requests.get('http://localhost:9200/tmdb/movie/_search', data=json.dumps(search))
searchHits = json.loads(httpResp.text)['hits']

print "Num\tRelevance Score\t\tMovie Title\t\tOverview"
for idx, hit in enumerate(searchHits['hits']):
        print "%s\t%s\t\t%s\t\t%s" % (idx + 1, hit['_score'], hit['_source']['title'], len(hit['_source']['overview']))


# Out[20]:

#     Num	Relevance Score		Movie Title		Overview
#     1	1.0134406		Space Jam		119
#     2	0.30218136		Grown Ups		138
#     3	0.28157377		The Flintstones		280
#     4	0.28157377		Speed Racer		280
#     5	0.25901258		White Men Can't Jump		221
#     6	0.25901258		Coach Carter		171
#     7	0.22431147		Semi-Pro		740
#     8	0.20171277		The Thing		125
#     9	0.17267506		High School Musical		435
#     10	0.17267506		Bedazzled		326
#     11	0.17115895		Meet Dave		191
#     12	0.16137022		Aliens vs Predator: Requiem		481
#     13	0.16137022		Escape from Planet Earth		127
#     14	0.16137022		The Darkest Hour		98
#     15	0.16137022		Invasion of the Body Snatchers		114
#     16	0.16137022		Slither		111
#     17	0.14263247		District 9		328
#     18	0.14119893		Avatar		175
#     19	0.14119893		The Last Starfighter		147
#     20	0.12934917		Alien		420
#     21	0.12934917		Aliens		357
#     22	0.12934917		Alien³		380
#     23	0.12451784		The Basketball Diaries		131
#     24	0.122281864		The X Files		708
#     25	0.122281864		Aliens in the Attic		617
#     26	0.12102766		Napoleon Dynamite		184
#     27	0.12102766		The Day the Earth Stood Still		183
#     28	0.12102766		Galaxy Quest		230
#     29	0.12102766		Outlander		213
#     30	0.12102766		Scary Movie 3		216
#     31	0.12102766		Titan A.E.		179
#     32	0.12102766		The Hitchhiker's Guide to the Galaxy		222
#     33	0.11410597		Star Trek IV: The Voyage Home		573
#     34	0.11410597		Independence Day		393
#     35	0.11410597		Ghosts of Mars		539
#     36	0.11410597		Dude, Where’s My Car?		398
#     37	0.11410597		Edge of Tomorrow		371
#     38	0.100856386		Contact		252
#     39	0.100856386		Star Trek: Insurrection		277
#     40	0.100856386		Predators		321
#     41	0.100856386		Mars Attacks!		289
#     42	0.100856386		AVP: Alien vs. Predator		344
#     43	0.100856386		Pitch Black		361
#     44	0.100856386		Batteries Not Included		249
#     45	0.100856386		Lifted		320
#     46	0.100856386		Scary Movie 4		224
#     47	0.100856386		Justice League: War		272
#     48	0.100856386		The Watch		313
#     49	0.100856386		Species		327
#     50	0.100856386		The Host		239
#     51	0.100856386		Under the Skin		249
#     52	0.100856386		Alien: Resurrection		260
#     53	0.09984273		Attack the Block		533
#     54	0.09984273		Battleship		606
#     55	0.080843225		Cowboys & Aliens		367
#     56	0.08068511		Predator		465
#     57	0.08068511		Predator 2		407
#     58	0.08068511		Men in Black		503
#     59	0.08068511		They Live		427
#     60	0.08068511		Battlefield Earth		394
#     61	0.08068511		The Faculty		441
#     62	0.08068511		The Day the Earth Stood Still		350
#     63	0.08068511		Short Circuit		349
#     64	0.08068511		Monsters		479
#     65	0.08068511		Lilo & Stitch		305
#     66	0.08068511		Spider-Man 3		357
#     67	0.08068511		Doom		459
#     68	0.08068511		Halo 4: Forward Unto Dawn		580
#     69	0.08068511		The Invasion		451
#     70	0.08068511		Riddick		471
#     71	0.08068511		Dreamcatcher		413
#     72	0.08068511		Spring Breakers		536
#     73	0.08068511		Paul		431
#     74	0.07059947		Men in Black II		634
#     75	0.07059947		Men in Black 3		572
#     76	0.07059947		Pride		673
#     77	0.07059947		Mars Needs Moms		537
#     78	0.07059947		There Will Be Blood		633
#     79	0.064674586		Monsters vs Aliens		333
#     80	0.06051383		Stalker		755
#     81	0.06051383		Wreck-It Ralph		658
# 

#!/usr/bin/env python
import sys
import json

def explainerize(explain,tab=0):
	value = explain.get("value",None)
	desc = explain.get("description",None)
	det = explain.get("details",None)
	if desc:
		print "{0}({1}) {2}".format(" "*2*tab,value,desc)
	if det:
		for sub_det in det:
			explainerize(sub_det,tab+1)


with sys.stdin as explain:
	data=explain.read()

data = json.loads(data)

hits = data.get("hits",None)
if hits:
	for i,hit in enumerate(hits["hits"]):
		print i
		explainerize(hit["_explanation"],1)
else:
	explainerize(data)

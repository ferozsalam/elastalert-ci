import argparse
import json
import os

from datetime import datetime
from elasticsearch import Elasticsearch

ES_USER = os.environ.get("ES_USER")
ES_PASSWORD = os.environ.get("ES_PASSWORD")
ES_HOST = os.environ.get("ES_HOST")
ES_PORT = os.environ.get("ES_PORT")

parser = argparse.ArgumentParser()
parser.add_argument('--index', type=str, required=True, help='Index to query against')
parser.add_argument('--query', type=str, required=True, help='Query to run')

args = parser.parse_args()
body = json.loads(args.query)

es = Elasticsearch([f"https://{ES_USER}:{ES_PASSWORD}@{ES_HOST}:{ES_PORT}"],
                   verify_certs=False)

res = es.search(index=args.index, body=body)

metadata = {
    "index": {
        "_id": 1
    }
}

for hit in res['hits']['hits']:
    print(json.dumps(metadata))
    print(json.dumps(hit['_source']))
    metadata["index"]["_id"] = metadata["index"]["_id"] + 1

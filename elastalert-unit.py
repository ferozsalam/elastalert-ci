#!/bin/python

import argparse
import json
import os
import requests
import subprocess
import time
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--data', type=str, help='File that contains data to match against')
parser.add_argument('--rule', type=str, help='File that contains rule to run')

args = parser.parse_args()

# Build request to upload test data to ES
if "ES_HOST" in os.environ:
    upload_url = "http://"+ os.environ["ES_HOST"] + ":9200/test/_bulk?pretty&refresh"
else:
    upload_url = "http://localhost:9200/test/_bulk?pretty&refresh"

headers = {'Content-Type': 'application/json'}
data = open(args.data, 'rb').read()

# Upload data to ES
res = requests.post(upload_url, headers=headers, data=data)

# Load rule to test against, change the index to our test index
with open(args.rule) as rule_file:
    rule_yaml = yaml.load(rule_file)

rule_yaml['index'] = 'test'

with open('rule_rewritten.yaml', 'w') as rewritten_rule_file:
    yaml.dump(rule_yaml, rewritten_rule_file)

subprocess.run(["elastalert-test-rule", "--formatted-output", "--config", "/data/config.yaml", 
                    "rule_rewritten.yaml"], check=True)

with open('output.json', 'r') as output_json:
    output = json.load(output_json)

if output["writeback"]["elastalert_status"]["matches"] > 0:
    exit(0)
else:
    exit(1)

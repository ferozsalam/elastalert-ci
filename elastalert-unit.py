#!/bin/python

import argparse
import requests
import subprocess
import time
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--data', type=str, help='File that contains data to match against')
parser.add_argument('--rule', type=str, help='File that contains rule to run')

args = parser.parse_args()

# Build request to upload test data to ES
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

subprocess.run(["elastalert-test-rule", "rule_rewritten.yaml"])

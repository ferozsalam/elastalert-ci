#!/bin/python

import argparse
import json
import os
import re
import requests
import subprocess
import time
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--data', type=str, help='File that contains data to match against')
parser.add_argument('--rule', type=str, help='File that contains rule to run')

args = parser.parse_args()

# Load rule to test against, change the index to our test index
with open(args.rule) as rule_file:
    rule_yaml = yaml.load(rule_file)
rule_yaml['index'] = 'test'
with open('rule_rewritten.yaml', 'w') as rewritten_rule_file:
    yaml.dump(rule_yaml, rewritten_rule_file)

with open(args.data) as data_files:
    data_files_yaml = yaml.load(data_files)

data = open(data_files_yaml[rule_yaml['ci_data']]["file"], 'rb').read()
headers = {'Content-Type': 'application/json'}

# Build request to upload test data to ES
if "ES_HOST" in os.environ:
    upload_url = "http://"+ os.environ["ES_HOST"] + ":9200/test/_bulk?pretty&refresh"
else:
    upload_url = "http://localhost:9200/test/_bulk?pretty&refresh"

# Upload data to ES
res = requests.post(upload_url, headers=headers, data=data)

elastalert_run = subprocess.run(["elastalert-test-rule",
                                  "--formatted-output",
                                  "--config", "/data/config.yaml",
                                  "--start", rule_yaml['ci_start_time'],
                                  "--end", rule_yaml['ci_end_time'],
                                  "rule_rewritten.yaml"], 
                                  capture_output=True,
                                  text=True,
                                  check=True)

alert_fired = re.search(":Alert for", elastalert_run.stderr)

filtered_stdout = elastalert_run.stdout.replace("Didn't get any results.\n1 rules loaded\n", "")
output = json.loads(filtered_stdout)

if (output["writeback"]["elastalert_status"]["matches"] > 0 and alert_fired):
    exit(0)
else:
    exit(1)

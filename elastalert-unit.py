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
parser.add_argument('--rules', nargs='+', type=str, help='File that contains rule to run')

args = parser.parse_args()

for rule_filename in args.rules:
    # Load rule to test against, change the index to our test index
    with open(rule_filename) as rule_file:
        rule = yaml.load(rule_file)

    try:
        data_source = rule["ci_data_source"]
    except:
        print("No data source defined for file, skipping")
        exit(0)

    rule['index'] = 'test'
    with open('rule_rewritten.yaml', 'w') as rewritten_rule_file:
        yaml.dump(rule, rewritten_rule_file)

    with open(args.data) as data_config_file:
        data_config = yaml.load(data_config_file)

    data = open(data_config[data_source]["filename"], 'rb').read()
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
                                      "--start", data_config[data_source]["start_time"],
                                      "--end", data_config[data_source]["end_time"],
                                      "rule_rewritten.yaml"], 
                                      capture_output=True,
                                      text=True,
                                      check=True)

    alert_fired = re.search(":Alert for", elastalert_run.stderr)

    filtered_stdout = elastalert_run.stdout.replace("Didn't get any results.\n1 rules loaded\n", "")
    print(filtered_stdout)
    output = json.loads(filtered_stdout)

    # Clear the ES index
    if "ES_HOST" in os.environ:
        delete_url = "http://"+ os.environ["ES_HOST"] + ":9200/test"
    else:
        delete_url = "http://localhost:9200/test/"
    delete_res = requests.delete(delete_url)

    if (output["writeback"]["elastalert_status"]["matches"] > 0 and alert_fired):
        exit(0)
    else:
        exit(1)

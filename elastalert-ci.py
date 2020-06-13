import argparse
import json
import os
import re
import requests
import subprocess
import time
import yaml

# Rewrite elements of a given rule to fit into the testing framework
def rewrite_rule(rule):
    # Use a single test index for all the data at the moment
    rule['index'] = 'test'

    # The Docker ES instance we spin up doesn't have SSL enabled, but all networking
    # is local, so this is not a security concern
    if 'use_ssl' in rule:
        rule['use_ssl'] = False

    with open('rule_rewritten.yaml', 'w') as rewritten_rule_file:
        yaml.dump(rule, rewritten_rule_file)

# docker-compose sets the hostname to be the service name, while CircleCI
# uses localhost for everything, so set the Elasticsearch hostname accordingly
def get_es_base_url():
    if "ES_HOST" in os.environ:
        es_base_url = "http://"+ os.environ["ES_HOST"] + ":9200/test/"
    else:
        es_base_url = "http://localhost:9200/test/"

    return es_base_url

def load_es_data(data):
    headers = {'Content-Type': 'application/json'}
    upload_url = get_es_base_url() + "_bulk?pretty&refresh"

    res = requests.post(upload_url, headers=headers, data=data)

def clear_test_index():
    delete_url = get_es_base_url() + "test/"
    delete_res = requests.delete(delete_url)

def rule_matched(raw_elastalert_output):
    filtered_stdout = raw_elastalert_output.replace("Didn't get any results.\n1 rules loaded\n", "")
    output = json.loads(filtered_stdout)

    return output["writeback"]["elastalert_status"]["matches"] > 0

def check_rule(rule, data_config):
    try:
        data_source = rule["ci_data_source"]
    except:
        print("No CI definition for rule, skipping")
        return True

    rewrite_rule(rule)

    data = open(data_config[data_source]["filename"], 'rb').read()
    load_es_data(data)

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
    if (alert_fired and rule_matched(elastalert_run.stdout)):
        return True
    else:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, help='File that contains data to match against')
    parser.add_argument('--rules', nargs='+', type=str, help='File that contains rule to run')

    args = parser.parse_args()

    with open(args.data) as data_config_file:
        data_config = yaml.safe_load(data_config_file)

    passed_rules = []
    failed_rules = []

    for rule_filename in args.rules:
        # Load rule to test against
        with open(rule_filename) as rule_file:
            rule = yaml.safe_load(rule_file)

        if (check_rule(rule, data_config)):
            passed_rules.append(rule["name"])
        else:
            failed_rules.append(rule["name"])

        clear_test_index()

    if len(failed_rules):
        print("Failed rules: " + str(failed_rules))
        exit(1)
    else:
        exit(0)

if __name__ == '__main__':
    main()

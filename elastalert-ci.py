import argparse
import json
import os
import re
import requests
import subprocess
import time
import yaml

# Rewrite elements of a given rule to fit into the testing framework
def rewrite_rule(rule, data_config):
    # Use a single test index for all the data at the moment
    rule['index'] = 'test'

    if ('ES_SCHEME' not in os.environ):
        scheme = 'http'
    else:
        scheme = os.environ.get('ES_SCHEME')

    if ('use_ssl' in rule) and (scheme == 'http'):
        rule['use_ssl'] = False

    rule['verify_certs'] = 'SKIP_SSL_VERIFY' in os.environ

    # Use a custom timestamp field if one is specified in the data source
    if 'timestamp_field' in data_config:
        rule['timestamp_field'] = data_config['timestamp_field']

    with open('rule_rewritten.yaml', 'w') as rewritten_rule_file:
        yaml.dump(rule, rewritten_rule_file)

# docker-compose sets the hostname to be the service name, while CircleCI
# uses localhost for everything, so set the Elasticsearch hostname accordingly
def get_es_base_url():

    scheme = 'http'
    if os.environ.get('ES_SCHEME'):
        scheme = os.environ.get('ES_SCHEME')

    if "ES_HOST" in os.environ:
        es_base_url = f"{scheme}://{os.environ['ES_HOST']}:9200/test/"
    else:
        es_base_url = f"{scheme}://localhost:9200/test/"

    return es_base_url

def load_es_data(data):
    headers = {'Content-Type': 'application/json'}
    upload_url = get_es_base_url() + "_bulk?pretty&refresh"
    skip_ssl_verify = "SKIP_SSL_VERIFY" in os.environ

    res = requests.post(upload_url, headers=headers, data=data, verify=(not skip_ssl_verify))
    res.raise_for_status()

def clear_test_index():
    delete_url = get_es_base_url()
    delete_res = requests.delete(delete_url)
    delete_res.raise_for_status()

def rule_matched(raw_elastalert_output):
    filtered_stdout = raw_elastalert_output.replace("Didn't get any results.\n1 rules loaded\n", "")
    output = json.loads(filtered_stdout)

    return output["writeback"]["elastalert_status"]["matches"] > 0

def check_rule(rule, data_config, data_directory):
    if "name" in rule:
        print(f'Testing {rule.get("name")}')
    else:
        print('No rule name found, skipping YAML file')
        return True

    data_sources = filter(lambda x : rule["name"] in data_config[x]["rules"], data_config)

    for data_source in data_sources:
        rewrite_rule(rule, data_config[data_source])

        filename = data_directory + '/' + data_config[data_source]["filename"]
        data = open(filename, 'rb').read()
        try:
            load_es_data(data)
        except requests.exceptions.HTTPError as e:
            print(f"Failed to load data from {filename} into Elasticsearch, exiting")
            exit(1)

        elastalert_run = subprocess.run(["elastalert-test-rule",
                                          "--formatted-output",
                                          "--config", "/data/config.yaml",
                                          "--start", data_config[data_source]["start_time"],
                                          "--end", data_config[data_source]["end_time"],
                                          "rule_rewritten.yaml"],
                                          capture_output=True,
                                          text=True,
                                          check=True)

        try:
            clear_test_index()
        except requests.exceptions.HTTPError:
            print("Failed to remove data from Elasticsearch, exiting")
            exit(1)

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

        try:
            if (check_rule(rule, data_config, os.path.dirname(args.data))):
                passed_rules.append(rule["name"])
            else:
                failed_rules.append(rule["name"])
        except Exception as e:
            print(f"YAML file failed rule checks, skipping")
            print(f"Detailed error:\n{e}")
            continue

    # Clean up
    if os.path.exists("rule_rewritten.yaml"):
        os.remove("rule_rewritten.yaml")

    if len(failed_rules):
        print("Failed rules: " + str(failed_rules))
        exit(1)
    else:
        exit(0)

if __name__ == '__main__':
    main()

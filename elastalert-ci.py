import argparse
import glob
import json
import logging
import os
import re
import requests
import subprocess
import sys
import yaml

# Rewrite elements of a given rule to fit into the testing framework
def rewrite_rule(rule, data_config):
    # Use a single test index for all the data at the moment
    rule['index'] = 'test'

    if ('ES_SCHEME' not in os.environ):
        scheme = 'http'
    else:
        scheme = os.environ.get('ES_SCHEME')

    rule.pop('aggregation', None)

    if ('use_ssl' in rule) and (scheme == 'http'):
        rule['use_ssl'] = False

    rule['verify_certs'] = not ('SKIP_SSL_VERIFY' in os.environ)

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

    if os.environ.get('ES_USERNAME'):
        res = requests.post(
                            upload_url,
                            headers=headers,
                            data=data,
                            verify=(not skip_ssl_verify),
                            auth=(
                                  os.environ.get('ES_USERNAME'),
                                  os.environ.get('ES_PASSWORD')
                                 )
                            )
    else:
        res = requests.post(upload_url, headers=headers, data=data, verify=(not skip_ssl_verify), auth=False)

    res.raise_for_status()

def clear_test_index():
    skip_ssl_verify = "SKIP_SSL_VERIFY" in os.environ

    delete_url = get_es_base_url()

    if os.environ.get('ES_USERNAME'):
        delete_res = requests.delete(delete_url,
                                     verify=(not skip_ssl_verify),
                                     auth=(
                                        os.environ.get('ES_USERNAME'),
                                        os.environ.get('ES_PASSWORD')
                                     )
                                    )
    else:
        delete_res = requests.delete(delete_url, verify=(not skip_ssl_verify))

    delete_res.raise_for_status()

def rule_matched(raw_elastalert_output):
    filtered_stdout = raw_elastalert_output.replace("Didn't get any results.\n1 rules loaded\n", "")
    output = json.loads(filtered_stdout)

    return output["writeback"]["elastalert_status"]["matches"] > 0

def check_rule(rule, data_config, data_directory):
    if "name" in rule:
        logging.info(f'Testing {rule.get("name")}')
    else:
        logging.info('No rule name found, skipping YAML file')
        return True

    data_sources = filter(lambda x : rule["name"] in data_config[x]["rules"], data_config)

    for data_source in data_sources:
        rewrite_rule(rule, data_config[data_source])

        filename = data_directory + '/' + data_config[data_source]["filename"]
        data = open(filename, 'rb').read()
        try:
            load_es_data(data)
        except requests.exceptions.HTTPError as e:
            logging.error(f"Failed to load data from {filename} into Elasticsearch, exiting")
            sys.exit(1)

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
        except requests.exceptions.HTTPError as e:
            logging.error("Failed to remove data from Elasticsearch, exiting")
            logging.error(e)
            sys.exit(1)

        alert_fired = re.search(":Alert for", elastalert_run.stderr)
        return (alert_fired and rule_matched(elastalert_run.stdout))

def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, help='File that contains data to match against')
    parser.add_argument('--rules_directory', type=str, help='Directory containing rules to run')

    args = parser.parse_args()

    with open(args.data) as data_config_file:
        data_config = yaml.safe_load(data_config_file)

    rules = glob.glob(f"{args.rules_directory}/*.yaml")

    passed_rules = []
    failed_rules = []

    for rule_filename in rules:
        # Load rule to test against
        with open(rule_filename) as rule_file:
            rule = yaml.safe_load(rule_file)

        try:
            data_directory = os.path.dirname(os.path.abspath(args.data))
            if (check_rule(rule, data_config, data_directory)):
                passed_rules.append(rule["name"])
                logging.info(f"Rule {rule['name']} passed!")
            else:
                failed_rules.append(rule["name"])
        except Exception as e:
            logging.info(f"Skipping file {rule_filename}. Error:\n{e}")
            continue

    # Clean up
    if os.path.exists("rule_rewritten.yaml"):
        os.remove("rule_rewritten.yaml")

    if len(passed_rules):
        logging.info(f"{len(passed_rules)} passed rules: " + str(passed_rules))
    if len(failed_rules):
        logging.info(f"{len(failed_rules)} failed rules: " + str(failed_rules))
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()

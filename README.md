# elastalert-ci

Continuous integration for Elastalert rules; compatible with Docker Compose,
Kubernetes, and CircleCI.

**Note**: This is an early version of a side-project. It might change rapidly,
or might not be updated at all; use it with this in mind. I would not recommend
using this image to anyone who is not already somewhat familiar with Elasticsearch,
ElastAlert, and Docker.

## What is this?

This repository provides a Docker image which you can use to create CI pipelines
for your ElastAlert detection rules.

This repo provides an example of how you can use Docker Compose - see the 
`docker-compose.yaml` for more details.

[elastalert-dummy-rules](https://github.com/ferozsalam/elastalert-dummy-rules)
provides an example of how you could use this image within a CircleCI pipeline.

![](https://padlock.argh.in/images/circleci.png)

Both the Docker Compose and CircleCI configuratiosn spin up an Elasticsearch
container and an ElastAlert container, uploads provided test data to the
Elasticsearch container, and then runs `elastalert-test-rule` against all the
rules that are provided to it. The results of `elastalert-test-rule` are passed
to a wrapper script that collects the results of all rules that have run,
returning a 0 exit code if all alerts have fired and a 1 exit code if any
rules haven't fired.

Key features:

- Works against all types of Elastalert rules, applying filters
  (unlike `elastalert-test-rule` when run with the `--data` flag)
- Designed to work recursively against all Elastalert rules in a folder
- Can ignore rules that don't have data to test against

Current limitations:

- Can currently only check for positive matches
- Can't check for a specific number of positive matches
- Can't check for specific output in the alert text
- Does not work with aggregations (but can check if an aggregated rule fires
  if the aggregation period is ignored)

## How do I use this?

Aside from the CircleCI config, there are three things you
will need to add to your existing repository of rules to make this work in your
repository:

1. Data to match against for each rule that you that you want to run CI processes
against.
    - Multiple rules can refer to the same data file, if this works for you.
    - See `data.json` for an example of how the data should be formatted; you
      can use `util/es-data-exporter.py` to create data in this format. See
      [this post][0] for an example of how to do this end to end.
    - These files can have any name you like, and can be located anywhere 
      in your repository of rules.
2. An index of data files, in the format of `data-files.yaml`. Each reference should have
   the following:
    - `filename`: The location of the data file relative to the repository root
    - `rules`: List of rules that you want to test against this data file
    - `start_time`: The timestamp of the earliest record in the dataset, in the format `YYYY-MM-DDThh:mm:ss`
    - `end_time`: The timestamp of the latest record in the dataset, in the format `YYYY-MM-DDThh:mm:ss`

Then define your Docker Compose/CircleCI configuration as required, using the examples
provided above as a guide.

[0]: https://padlock.argh.in/2020/10/04/elastalert-ci-example.html
[1]: https://github.com/ferozsalam/elastalert-dummy-rules/blob/master/.circleci/config.yml

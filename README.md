# elastalert-ci

Parallelisable continuous integration for Elastalert rules using CircleCI.

**2020-05-16**: This is an early version of a side-project. It might change rapidly,
or might not be updated at all; use it with this in mind. I would not recommend
using this image to anyone who is not already somewhat familiar with Elasticsearch,
Elastalert, and Docker.

## What is this?

This repository provides a CircleCI-compatible convenience image that you can
use to test your Elastalert rules.

[elastalert-dummy-rules](https://github.com/ferozsalam/elastalert-dummy-rules)
provides an example of how you could use this image within a CircleCI pipeline.

![](https://padlock.argh.in/images/circleci.png)

The CI configuration spins up an Elasticsearch container and an Elastalert 
container, uploads provided test data to the Elasticsearch container, and then
runs `elastalert-test-rule` against all the rules that are provided to it.
The results of `elastalert-test-rule` are passed to a wrapper script that
collects the results of all rules that have run, returning a 0 exit code if all
alerts have fired and a 1 exit code if any rules haven't fired.

Key features:

- Works against all types of Elastalert rules, applying filters
  (unlike `elastalert-test-rule` when run with the `--data` flag)
- Designed to work recursively against all Elastalert rules in a folder
- Designed to work using CircleCI's parallelism features
- Can ignore rules that don't have data to test against

Current limitations:

- Can currently only check for positive matches
- Can't check for a specific number of positive matches
- Can't check for specific output in the alert text
- Can only check a rule against a single data file

## How do I use this?

Aside from the CircleCI config, there are three things you
will need to add to your existing repository of rules to make this work in your
repository:

1. Data to match against for each rule that you that you want to run CI processes
against.
    - Multiple rules can refer to the same data file, if this works for you.
    - See `data.json` for an example of how the data should be formatted; essentially
      you should be able to `POST` the contents of the data files to Elasticsearch
      without modification.
    - These files can have any name you like, and can be located anywhere 
      in your repository of rules.
2. An index of data files, in the format of `data-files.yaml`. Each reference should have
   the following:
    - `filename`: The location of the data file relative to the repository root
    - `start_time`: The timestamp of the earliest record in the dataset, in the format `YYYY-MM-DDThh:mm:ss`
    - `end_time`: The timestamp of the latest record in the dataset, in the format `YYYY-MM-DDThh:mm:ss`
3. An extra `ci_data_source` field in your rule definition that points to the 
   relevant dataset as defined in your index.

If you want to ignore a particular rule, simply don't set the `ci_data_source`, and
the test wrapper will ignore it.

Finally, define your CircleCI configuration. Something like what has been defined for
[elastalert-dummy-rules][1] should work for you.

## How do I test this image locally?

`docker-compose` functionality has been provided for illustrative purposes.

To test:

1. Clone this repo
2. Run `docker-compose build`
3. Run `docker-compose up --abort-on-container-exit`

A successful run will eventually output something like:

```
elastalertci_elastalert-ci_1 exited with code 0
```

A zero exit code means that your rule matched the provided data; a non-zero exit
code means that the rule either didn't match or something else went wrong.

Edit your `rule.yaml`, `data-files.yaml`, and `data.json` as required to test
various different rule and data structures.

[1]: https://github.com/ferozsalam/elastalert-dummy-rules/blob/master/.circleci/config.yml

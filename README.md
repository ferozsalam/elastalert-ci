This image provides a rough and ready way to test an Elastalert rule against
Elasticsearch logs.

This is currently a work in progress; once completed, the image will be useable
as part of a CircleCI pipeline.

`docker-compose` funcionality has been provided for illustrative purposes only.

To test:

1. Clone this repo
2. Create a `rule.yaml` in the repo root with your Elastalert rule
3. Create a `data.json` with the logs you want to test against in JSON format
4. Run `docker-compose build`
5. Run `docker-compose up`

A successful run will eventually output something like:

```
elastalert-unit_1  | elastalert_status - {'rule_name': 'Dummy rule', 'endtime': datetime.datetime(2020, 5, 10, 16, 24, 40, 925124, tzinfo=tzutc()), 'starttime': datetime.datetime(2020, 5, 9, 16, 24, 40, 925124, tzinfo=tzutc()), 'matches': 1, 'hits': 1, '@timestamp': datetime.datetime(2020, 5, 10, 16, 24, 42, 221058, tzinfo=tzutc()), 'time_taken': 1.0156700611114502}
elastalert-unit_1  |
elastalertunit_elastalert-unit_1 exited with code 0
```

## How it works

Spins up an Elasticsearch container and an Elastalert container, uploads provided test
data to the Elasticsearch container, and then runs `elastalert-test-rule` using the
provided rule against the uploaded data.

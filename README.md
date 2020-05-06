This image provides a rough and ready way to test an Elastalert rule against
Elasticsearch logs.

To test:

1. Clone this repo
2. Create a `rule.yaml` in the repo root with your Elastalert rule
3. Create a `data.json` with the logs you want to test against in JSON format
4. Run `docker-compose build`
5. Run `docker-compose up`

A successful run will output something like:

```
elastalert-unit_1  | elastalert_status - {'rule_name': 'Test Rule', 'endtime': datetime.datetime(2020, 4, 15, 14, 8, 45, 881000, tzinfo=tzlocal()), 'starttime': datetime.datetime(2020, 4, 15, 14, 8, 44, 881000, tzinfo=tzlocal()), 'matches': 1, 'hits': 0, '@timestamp': datetime.datetime(2020, 5, 6, 18, 59, 17, 812561, tzinfo=tzutc()), 'time_taken': 0.018953800201416016}
elastalert-unit_1  |
elastalert-unit_1  | 2020/05/06 18:59:17 Command finished successfully.
elastalertunit_elastalert-unit_1 exited with code 0
```

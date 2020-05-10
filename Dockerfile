FROM python:3.6-buster

LABEL description="Elastalert unit testing module"
LABEL maintainer="Feroz Salam (feroz@argh.in)"

RUN pip install elastalert

# Required CircleCI dependencies
RUN apt update && \
    apt install -y git ssh tar gzip ca-certificates

# Need to do this because of https://github.com/Yelp/elastalert/issues/2781
RUN sed -i 's/string.letters/string.ascii_letters/g' /usr/local/lib/python3.6/site-packages/elastalert/test_rule.py

RUN wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-v0.6.1.tar.gz
RUN tar -C /usr/local/bin -xvzf dockerize-linux-amd64-v0.6.1.tar.gz

WORKDIR /data

CMD ["dockerize", "-wait", "http://elasticsearch:9200/_cluster/health", "-timeout", "120s", \
            "python", "elastalert-unit.py", "--data", "/data/data.json", "--rule", "rule.yaml"]

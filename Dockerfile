FROM python:3.8-buster

LABEL description="Elastalert CI testing module"
LABEL maintainer="Feroz Salam (feroz@argh.in)"

RUN pip install elastalert

# Required CircleCI dependencies
RUN apt update && \
    apt install -y git ssh tar gzip ca-certificates

COPY custom_test_rule.py /usr/local/lib/python3.6/site-packages/elastalert/test_rule.py

RUN wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-v0.6.1.tar.gz
RUN tar -C /usr/local/bin -xvzf dockerize-linux-amd64-v0.6.1.tar.gz

WORKDIR /data

COPY elastalert-ci.py /data
COPY config.yaml /data

CMD ["dockerize", "-wait", "http://elasticsearch:9200/_cluster/health", "-timeout", "120s", \
            "python", "elastalert-ci.py", "--data", "data-files.yaml", "--rules", "rule.yaml"]

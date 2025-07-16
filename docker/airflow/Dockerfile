FROM apache/airflow:2.9.3-python3.11

ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.11

RUN set -ex \
 && curl -Lf "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt" \
      -o /tmp/constraints.txt \
 && pip install --no-cache-dir --constraint /tmp/constraints.txt \
      apache-airflow-providers-apache-kafka \
      apache-airflow-providers-apache-spark

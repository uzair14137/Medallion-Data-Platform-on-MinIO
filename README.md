# Medallion Data Platform on MinIO

A self-contained proof-of-concept demonstrating a Medallion-style data lake architecture on MinIO (Delta Lake), ingesting both streaming and batch sources, transforming with Apache Spark, and serving to BI/ML layers via Trino and Superset.

```mermaid
flowchart TD
  subgraph Ingestion
    K[Kafka<br/>• user_profiles, user_posts, user_follows]
    S[Sqoop<br/>• Relational batch]
    T[Trino<br/>• Federated sources]
    K & S & T --> Spark["Apache Spark<br/>Structured Streaming &amp; Batch"]
  end

  Spark -->|Delta Lake on MinIO| MinIO[(MinIO<br/>Delta Lake)]

  subgraph Serving
    MinIO -->|Federated Queries| Trino2[Trino]
    Trino2 --> Superset[Superset<br/>• BI Dashboards]
    MinIO --> ML["ML Workbench<br/>Data Science"]
  end

  subgraph Graph_Metrics
    Spark --> Janus[JanusGraph<br/>Gremlin API]
    Spark --> ClickHouse[ClickHouse<br/>Low-latency analytics]
  end

  subgraph Orchestration
    Airflow[Airflow DAGs] -->|Schedule &amp; Retry| Spark
  end

  subgraph Governance
    OpenMeta[Open Metadata] --> |Catalog &amp; Lineage| MinIO
  end
```

Repository: https://github.com/uzair14137/Medallion-Data-Platform-on-MinIO

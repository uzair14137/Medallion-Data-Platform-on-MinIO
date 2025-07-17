# scripts/jobs/bronze_to_silver_batch.py
from datetime import datetime
from pathlib import PurePosixPath
from pyspark.sql import SparkSession, functions as F

# -------- configuration -------------------------------------------------
BRONZE_ROOT = "s3a://bronze-raw/social"     # no trailing slash
SILVER_ROOT = "s3a://silver-curated"
NESSIE_URI  = "http://nessie:19120/api/v1"
TOPICS      = [                            # folders you’ve seen in MinIO
    "twitter-posts",
    "twitter-followers",
    "twitter-following",
    "twitter-profile-information",
    "keybase-twitter",
]
# ------------------------------------------------------------------------

spark = (SparkSession.builder
         .appName("bronze→silver-batch")
         # Iceberg + Nessie
         .config("spark.sql.catalog.nessie", "org.apache.iceberg.spark.SparkCatalog")
         .config("spark.sql.catalog.nessie.warehouse", SILVER_ROOT)
         .config("spark.sql.catalog.nessie.uri", NESSIE_URI)
         .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
         .getOrCreate())

spark.sql("SET spark.sql.session.timeZone = UTC")
spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.silver")
spark.sql("USE nessie")
for topic in TOPICS:
    # --- 1. build a recursive glob:  topic=<topic>/year=*/month=*/day=*/*.json
    glob = (f"{BRONZE_ROOT}/topic={topic}"
            "/year=*/month=*/day=*/*.json")

    df = spark.read.json(glob)

    if df.isEmpty():
        print(f"[{datetime.utcnow()}]  {topic}: no new files")
        continue

    print(f"[{datetime.utcnow()}]  {topic}: read {df.count()} rows")

    # --- 2. enrich + write to Iceberg -----------------------------------
    (df
     .withColumn("topic", F.lit(topic))
     .withColumn("ingest_ts", F.to_timestamp("ingest_ts"))
     .withColumn("date_hour", F.date_format("ingest_ts", "yyyy-MM-dd-HH"))
     .writeTo(f"nessie.silver.{topic.replace('-', '_')}")
     .using("iceberg")
     .tableProperty("format-version", "2")
     .tableProperty("write.format.default", "parquet")
     .partitionedBy("date_hour")
     .createOrReplace())

    print(f"[{datetime.utcnow()}]  {topic}: upsert complete")

spark.stop()


# docker exec -it medallion-data-platform-on-minio-spark-master-1 \
#   spark-submit --packages \
#       org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2 \
#       /opt/bitnami/spark/jobs/bronze_to_silver_batch.py

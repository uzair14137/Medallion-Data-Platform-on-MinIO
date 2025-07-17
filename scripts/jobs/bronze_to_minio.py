from pyspark.sql import SparkSession, functions as F

spark = (SparkSession.builder
         .appName("bronze-social")
         .getOrCreate())

# 1 — subscribe to many topics at once
#     • subscribe = exact list  (“twitter-posts,ig-posts,tiktok-posts”)  OR
#     • subscribePattern = ".*-posts"        # regex
raw = (spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "10.100.102.137:9092")
        .option("subscribe","twitter-posts,twitter-following,twitter-followers,twitter-profile-information,keybase-twitter")   # any topic that ends -posts
        .option("startingOffsets", "earliest")
        .load())

# 2 — add routing columns
bronze = (raw
    .withColumn("payload",  F.col("value").cast("string"))
    .withColumn("ingest_ts", F.current_timestamp())
    .withColumn("year",  F.date_format("ingest_ts", "yyyy"))
    .withColumn("month", F.date_format("ingest_ts", "MM"))
    .withColumn("day",   F.date_format("ingest_ts", "dd"))
    .select("topic", "payload", "ingest_ts", "year", "month", "day"))

# 3 — write once, Spark builds the full folder tree
(bronze.writeStream
       .format("json")                # or parquet
       .partitionBy("topic", "year", "month", "day")
       .option("path", "s3a://bronze-raw/social")
       .option("checkpointLocation",
               "s3a://bronze-raw/_checkpoints/social_multi")
       .trigger(processingTime="30 seconds")
       .start()
       .awaitTermination())





# docker exec -it medallion-data-platform-on-minio-spark-master-1 \
#   spark-submit \
#     --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.kafka:kafka-clients:3.5.1 \
#     --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
#     --conf spark.hadoop.fs.s3a.access.key=minio \
#     --conf spark.hadoop.fs.s3a.secret.key=minio123 \
#     --conf spark.hadoop.fs.s3a.path.style.access=true \
#     --conf spark.kafka.bootstrap.servers=10.100.102.137:9092 \
#     /opt/bitnami/spark/jobs/bronze_to_minio.py

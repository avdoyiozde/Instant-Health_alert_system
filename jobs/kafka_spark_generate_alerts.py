from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import current_timestamp, to_json, struct

# Configuration parameters
checkpoint_path = "health-alert/alert_checkpoint/"
kafka_topic = "alerts_message"
kafka_servers = "localhost:9092"

# Initialize Spark session with Hive support
spark = SparkSession.builder \
    .appName("HealthAlertSystem") \
    .enableHiveSupport() \
    .getOrCreate()

# Define schema for patients vital data
schema = StructType([
    StructField('customerId', IntegerType(), True),
    StructField('heartBeat', IntegerType(), True),
    StructField('bp', IntegerType(), True),
    StructField('message_time', TimestampType(), True),
])

# Load static tables and cache them for performance
patients_contact_info = spark.table("health.patients_contact_info").cache()
threshold_ref = spark.table("health.threshold_ref").cache()

# Load streaming data from HDFS
patients_vital_data = spark.readStream \
    .format("parquet") \
    .schema(schema) \
    .load("health-alert/patients-vital-info/")

# Join streaming data with cached static tables and filter alert conditions
alert_df = patients_vital_data.alias("V") \
    .join(patients_contact_info.alias("C"), col("C.patientid") == col("V.customerId")) \
    .join(threshold_ref.alias("T"),
          (col("C.age").between(col("T.low_age_limit"), col("T.high_age_limit"))) &
          (
              (col("T.attribute") == "bp") & col("V.bp").between(col("T.low_range_value"), col("T.high_range_value")) |
              (col("T.attribute") == "heartBeat") & col("V.heartBeat").between(col("T.low_range_value"), col("T.high_range_value"))
          ) &
          (col("T.alert_flag") == 1)
    ) \
    .select(
        col("C.patientname"),
        col("C.age"),
        col("C.patientaddress"),
        col("C.phone_number"),
        col("C.admitted_ward"),
        col("V.bp").alias("bp"),
        col("V.heartBeat").alias("heartBeat"),
        col("V.message_time").alias("input_message_time"),
        col("T.alert_message"),
        current_timestamp().alias("generated_time")
    )

# Convert to JSON format for Kafka and write to Kafka topic
alert_df \
    .selectExpr("to_json(struct(*)) AS value") \
    .writeStream \
    .format("kafka") \
    .outputMode("append") \
    .option("kafka.bootstrap.servers", kafka_servers) \
    .option("topic", kafka_topic) \
    .option("checkpointLocation", checkpoint_path) \
    .start() \
    .awaitTermination()

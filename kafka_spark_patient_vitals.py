from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp
from pyspark.sql.types import StructType, StructField, IntegerType

# Configuration
storage_path = "health-alert/patients-vital-info/"
checkpoint_path = "health-alert/cp-vital-info/"
kafka_topic = "patients_vital_info"
kafka_servers = "localhost:9092"

# Initialize Spark Session
spark = SparkSession.builder \
    .master("local") \
    .appName("VitalInfoConsumer") \
    .enableHiveSupport()\
    .getOrCreate()


spark.sparkContext.setLogLevel('ERROR')

# Define Schema for Incoming Kafka Messages
vital_info_schema = StructType([
    StructField('customerId', IntegerType(), True),
    StructField('heartBeat', IntegerType(), True),
    StructField('bp', IntegerType(), True)
])

# Read Stream from Kafka Topic
vital_info_raw_stream = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_servers) \
    .option("subscribe", kafka_topic) \
    .option("startingOffsets", "earliest") \
    .load()

# Transform Data and Apply Schema
vital_info_df = vital_info_raw_stream \
    .select(from_json(col("value").cast("string"), vital_info_schema).alias("data")) \
    .select("data.*") \
    .withColumn("message_time", current_timestamp())

# Write to Console for Debugging
vital_info_stream_console = vital_info_df \
    .writeStream \
    .format("console") \
    .option("truncate", "false") \
    .trigger(processingTime="10 seconds") \
    .start()

# Write Stream to HDFS in Parquet Format
vital_info_stream_storage = vital_info_df \
    .writeStream \
    .format("parquet") \
    .option("path", storage_path) \
    .option("checkpointLocation", checkpoint_path) \
    .trigger(processingTime="10 seconds") \
    .start()

# Await Termination for Both Streams
vital_info_stream_console.awaitTermination()

vital_info_stream_storage.awaitTermination()

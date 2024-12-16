# Import necessary libraries
import boto3
import json
from kafka import KafkaConsumer
from botocore.exceptions import ClientError

# Kafka consumer configuration
consumer = KafkaConsumer(
    'alerts_message',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,  # Automatically commit offsets
    group_id='alert_consumer_group',  # Consumer group ID for managing offsets
    value_deserializer=lambda m: m.decode('utf-8')
)

# Initialize SNS client
sns_client = boto3.client(
    'sns',
    region_name='us-east-1',
    aws_access_key_id='',
    aws_secret_access_key=''
)
sns_topic_arn = ''

# Function to publish messages to SNS
def publish_to_sns(message_obj):
    subject_header = f"Health Alert: Patient- {message_obj.get('patientname', 'Unknown')}"
    try:
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps(message_obj),  # Convert the message object to a JSON string
            Subject=subject_header
        )
        print(f"Alert published for patient: {message_obj.get('patientname', 'Unknown')}")
    except ClientError as e:
        print(f"Failed to publish to SNS: {e}")

# Main loop to consume messages
for message in consumer:
    try:
        # Attempt to decode and load the message content as JSON
        message_obj = json.loads(message.value)
        publish_to_sns(message_obj)
    except json.JSONDecodeError as e:
        print(f"Error decoding message: {e}")
    except KeyError:
        print("Invalid message format received.")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Import necessary libraries
import boto3
import json
from kafka import KafkaConsumer
from botocore.exceptions import ClientError

# Kafka consumer configuration
consumer = KafkaConsumer(
    'Alerts_Message',
    bootstrap_servers=['ec2-44-196-94-216.compute-1.amazonaws.com:9092'],
    auto_offset_reset='earliest',
    value_deserializer=lambda m: m.decode('utf-8')
)

# Initialize SNS client
sns_client = boto3.client('sns', region_name='us-east-1')
sns_topic_arn = 'arn:aws:sns:us-east-1:284159339388:health-care-notification-system'
messages=["abc","pqr"]
# Publish messages to SNS topic
for message in messages:
    try:
        message_obj = json.loads(message.value)
        subject_header = f"Health Alert: Patient- {message_obj.get('patientname', 'Unknown')}"
        
        # Publish to SNS
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message="json.dumps(message_obj)",
            Subject=subject_header
        )
        print(f"Alert published for patient: {message_obj['patientname']}")
        
    except ClientError as e:
        print(f"Failed to publish to SNS: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding message: {e}")
    except KeyError:
        print("Invalid message format received.")

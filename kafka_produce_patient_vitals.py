import mysql.connector
from mysql.connector import Error
from kafka import KafkaProducer
import json
import time

HOST = 'upgraddetest.cyaielc9bmnf.us-east-1.rds.amazonaws.com'
DATABASE = 'testdatabase'
USER = 'student'
PASSWORD = 'STUDENT123'
TOPIC='patients_vital_info'
KAFKA_BOOTSTRAP_SERVERS='localhost:9092'
producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, value_serializer=lambda x: json.dumps(x).encode('utf-8'))  

def check_connection(host, database, user, password):
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
    return None

def fetch_data(host, database, user, password):
    connection = check_connection(host, database, user, password)
    if connection is None:
        print("Failed to connect to the database.")
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM patients_vital_info')
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"Error while fetching data: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def produce_to_kafka(data,topic):
    if not data:
        print("No data to produce.")
        return
    try:
        for row in data:
            data_dict = {
                'customerId': row[0],  
                'heartBeat': row[1],
                'bp': row[2],
            }
            print(data_dict)
            producer.send(topic, data_dict)
            time.sleep(1)
        producer.flush()
        print("Data produced successfully.")
    except Exception as e:
        print(f"Error producing data: {e}")

if __name__ == "__main__":
    data = fetch_data(HOST, DATABASE, USER, PASSWORD)
    produce_to_kafka(data,TOPIC)

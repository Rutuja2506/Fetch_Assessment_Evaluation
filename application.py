import boto3
import json
import hashlib
import psycopg2  
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Access SQS configuration from environment variables
sqs_endpoint_url = os.environ.get("SQS_ENDPOINT_URL")
sqs_queue_url = os.environ.get("SQS_QUEUE_URL")

# Configure the AWS SDK to use the LocalStack endpoint
sqs = boto3.client('sqs', endpoint_url=sqs_endpoint_url)

# Replace '<queue_url>' with the actual URL of your SQS Queue
queue_url = sqs_queue_url


# Access database configuration from environment variables
db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")
db_host = os.environ.get("DB_HOST")
db_port = os.environ.get("DB_PORT")
db_name = os.environ.get("DB_NAME")

# Establish a connection to the PostgreSQL database
try:
    connection = psycopg2.connect(
        user = db_user,
        password = db_password,
        host = db_host,
        port = db_port,
        database= db_name
    )
    cursor = connection.cursor()
    print("Connected to PostgreSQL database")
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL:", error)

# Alter the column type for 'app_version' if needed
alter_column_query = """
    ALTER TABLE user_logins
    ALTER COLUMN app_version TYPE VARCHAR;
"""
try:
    cursor.execute(alter_column_query)
    connection.commit()
    print("Column 'app_version' type altered to VARCHAR")
except (Exception, psycopg2.Error) as error:
    print("Error while altering column type:", error)
   
# Retrieve all messages from the queue
messages = []
while True:
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)
    # print(len(response))
    if 'Messages' not in response:
        break
    messages += response['Messages']
    
# print(len(messages))
# Define a function to mask PII data
def mask_pii(data):
    # Create a hash of the original data for easy duplicate identification
    hashed_data = hashlib.sha256(data.encode()).hexdigest()
    
    # Replace the original data with the hashed value
    return hashed_data

# # Process and mask the retrieved messages
for message in messages:
    # Parse the JSON message
    message_body = json.loads(message['Body'])
    
    # Check if 'device_id' exists in the message body before masking
    if 'device_id' in message_body:
        message_body['device_id'] = mask_pii(message_body['device_id'])
    
    # Check if 'ip' exists in the message body before masking
    if 'ip' in message_body:
        message_body['ip'] = mask_pii(message_body['ip'])
    
    # # Mask the 'device_id' and 'ip' fields
    # message_body['device_id'] = mask_pii(message_body['device_id'])
    # message_body['ip'] = mask_pii(message_body['ip'])
    
     # Parse and convert app_version to an integer
    app_version = message_body.get('app_version', None)
    
    # Convert the message back to JSON format
    masked_message = json.dumps(message_body)
    
    # Print or do something with the masked message
    print("Masked message:", masked_message)
    
    
    # Insert the masked message into the 'user_logins' table
    insert_query = """
    INSERT INTO user_logins (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)
    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE);
    """
  

    data = (
        message_body.get('user_id', None),
        message_body.get('device_type', None),
        message_body.get('ip', None),
        message_body.get('device_id', None),
        message_body.get('locale', None),
        app_version
        # message_body.get('app_version', None)
    )
    cursor.execute(insert_query, data)
    connection.commit()


    # Delete the message from the queue to avoid processing it again
    receipt_handle = message['ReceiptHandle']
    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
# Close the database connection
if connection:
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")
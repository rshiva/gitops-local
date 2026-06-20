import os

from boto3 import resource
from dotenv import load_dotenv

load_dotenv()

def get_dynamodb_resource():
    return resource("dynamodb",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("REGION_NAME", "us-east-1"),
        # CRITICAL: Let it be None if not set. Moto requires endpoint_url=None
        endpoint_url=os.getenv("AWS_DYNAMODB_ENDPOINT_URL")
    )

dynamodb = get_dynamodb_resource()

tables = [
  {
    "TableName": "users",
    "KeySchema": [
      {"AttributeName": "id", "KeyType": "HASH"},
      {"AttributeName": "created_at", "KeyType": "RANGE"}
    ],
    "AttributeDefinitions": [
      {"AttributeName": "id", "AttributeType": "S"},
      {"AttributeName": "created_at", "AttributeType": "S"}
    ]
  }
]

def create_tables(db_resource=None):
    db = db_resource or dynamodb
    for table_def in tables:
        try:
            db.create_table(
                TableName=table_def["TableName"],
                KeySchema=table_def["KeySchema"],
                AttributeDefinitions=table_def["AttributeDefinitions"],
                BillingMode="PAY_PER_REQUEST"
            )
            # Wait for table to be ACTIVE
            waiter = db.meta.client.get_waiter("table_exists")
            waiter.wait(TableName=table_def["TableName"])
        except db.meta.client.exceptions.ResourceInUseException:
            pass  # Already exists
        except Exception as e:
            print(f"❌ Failed to create table: {e}")
            raise

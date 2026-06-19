from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from fastapi.responses import JSONResponse

from .db import get_dynamodb_resource


def get_table():
    return get_dynamodb_resource().Table("users")

def create_user(user: dict):
    table = get_table()
    try:
        table.put_item(Item=user)
        return user
    except ClientError as e:
        print(f"❌ create_user error: {e.response['Error']['Message']}")
        return JSONResponse(content={"error": e.response["Error"]["Message"]}, status_code=500)

def get_user(id: str):
    table = get_table()
    try:
        response = table.query(KeyConditionExpression=Key("id").eq(id))
        return response["Items"]
    except ClientError as e:
        print(f"❌ get_user error: {e.response['Error']['Message']}")
        return JSONResponse(content={"error": e.response["Error"]["Message"]}, status_code=500)

def get_users():
    table = get_table()
    try:
        # ✅ Fixed: Use ProjectionExpression instead of deprecated AttributesToGet
        response = table.scan(
            Limit=5,
            ProjectionExpression="id, username"
        )
        return response["Items"]
    except ClientError as e:
        print(f"❌ get_users error: {e.response['Error']['Message']}")
        return JSONResponse(content={"error": e.response["Error"]["Message"]}, status_code=500)

def delete_user(user: dict):
    table = get_table()
    try:
        return table.delete_item(Key={"id": user["id"], "created_at": user["created_at"]})
    except ClientError as e:
        print(f"❌ delete_user error: {e.response['Error']['Message']}")
        return JSONResponse(content={"error": e.response["Error"]["Message"]}, status_code=500)

def update_user(user: dict):
    table = get_table()
    try:
        return table.update_item(
            Key={"id": user["id"], "created_at": user["created_at"]},
            UpdateExpression="SET username = :username, age = :age",
            ExpressionAttributeValues={":username": user["username"], ":age": user["age"]},
            ReturnValues="ALL_NEW"
        )
    except ClientError as e:
        print(f"❌ update_user error: {e.response['Error']['Message']}")
        return JSONResponse(content={"error": e.response["Error"]["Message"]}, status_code=500)

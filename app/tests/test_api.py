import os
import uuid

import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from database.db import create_tables, get_dynamodb_resource
from main import app

# --- Fixtures ---

@pytest.fixture(scope="function")
def aws_credentials():
    """Sets up mock AWS credentials and removes real endpoint URL to allow Moto to intercept."""
    old_environ = dict(os.environ)
    os.environ.update({
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SECURITY_TOKEN": "testing",
        "AWS_SESSION_TOKEN": "testing",
        "AWS_DEFAULT_REGION": "us-east-1",
        "REGION_NAME": "us-east-1",
    })
    # Crucial: Remove endpoint URL so boto3 doesn't try to hit localhost/docker
    os.environ.pop("AWS_DYNAMODB_ENDPOINT_URL", None)
    yield
    os.environ.clear()
    os.environ.update(old_environ)

@pytest.fixture(scope="function")
def setup_dynamodb(aws_credentials):
    """Creates a fresh DynamoDB table in Moto for each test function."""
    with mock_aws():
        mock_db = get_dynamodb_resource()
        create_tables(db_resource=mock_db)
        yield mock_db
        # Cleanup: Delete table to ensure test isolation
        try:
            mock_db.Table("users").delete()
        except Exception:
            pass

def get_client():
    return TestClient(app)

# --- Tests ---

def test_create_user_success(setup_dynamodb):
    client = get_client()
    user_data = {"username": "alice", "age": 30}

    response = client.post("/user/create", json=user_data)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "alice"
    assert data["age"] == 30
    assert "id" in data
    assert "created_at" in data
    # Verify ID is a valid UUID string format (basic check)
    try:
        uuid.UUID(data["id"])
    except ValueError:
        pytest.fail("ID is not a valid UUID")

def test_create_user_missing_fields(setup_dynamodb):
    client = get_client()
    # Missing 'age' which is required by Pydantic model
    user_data = {"username": "bob"}

    response = client.post("/user/create", json=user_data)

    # FastAPI/Pydantic should return 422 Unprocessable Entity for validation errors
    assert response.status_code == 422

def test_get_user_by_id_success(setup_dynamodb):
    client = get_client()

    # 1. Create a user first
    create_resp = client.post("/user/create", json={"username": "charlie", "age": 25})
    created_user = create_resp.json()
    user_id = created_user["id"]

    # 2. Get by ID
    response = client.get(f"/user/get/{user_id}")

    assert response.status_code == 200
    data = response.json()
    # get_user returns a list of items from Query
    assert len(data) > 0
    # Find the specific item (Query might return multiple if sort keys match, but ID is unique hash)
    found_user = next((u for u in data if u["id"] == user_id), None)
    assert found_user is not None
    assert found_user["username"] == "charlie"

def test_get_user_by_id_not_found(setup_dynamodb):
    client = get_client()
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/user/get/{fake_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # Should return empty list if not found

def test_update_user_success(setup_dynamodb):
    client = get_client()

    # 1. Create
    create_resp = client.post("/user/create", json={"username": "dave_old", "age": 40})
    created_user = create_resp.json()

    # 2. Update
    update_payload = {
        "id": created_user["id"],
        "created_at": created_user["created_at"],
        "username": "dave_new",
        "age": 41
    }
    response = client.put("/user/update", json=update_payload)

    assert response.status_code == 200

    # 3. Verify Update
    get_resp = client.get(f"/user/get/{created_user['id']}")
    updated_user_list = get_resp.json()
    updated_user = updated_user_list[0]

    assert updated_user["username"] == "dave_new"
    assert updated_user["age"] == 41
    # Ensure ID and created_at didn't change
    assert updated_user["id"] == created_user["id"]
    assert updated_user["created_at"] == created_user["created_at"]

def test_delete_user_success(setup_dynamodb):
    client = get_client()

    # 1. Create
    create_resp = client.post("/user/create", json={"username": "eve", "age": 29})
    created_user = create_resp.json()

    # 2. Delete
    delete_payload = {
        "id": created_user["id"],
        "created_at": created_user["created_at"],
        "username": "eve", # Not strictly needed for key, but part of User model
        "age": 29
    }
    response = client.request("DELETE", "/user/delete", json=delete_payload)

    assert response.status_code == 200

    # 3. Verify Deletion
    get_resp = client.get(f"/user/get/{created_user['id']}")
    assert get_resp.status_code == 200
    assert len(get_resp.json()) == 0

def test_health_check(setup_dynamodb):
    client = get_client()
    response = client.get("/user/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

import pytest
import io
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as c:
        yield c

def csv_file(content="name,age,salary\nAlice,25,50000\nBob,30,60000\n"):
    return (io.BytesIO(content.encode()), "test.csv")

def test_index_returns_html(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"html" in res.data.lower()

def test_upload_valid_csv(client):
    data = {"file": csv_file()}
    res = client.post("/api/upload", data=data,
                      content_type="multipart/form-data")
    assert res.status_code == 200
    body = res.get_json()
    assert body["rows"] == 2
    assert body["cols"] == 3
    assert "name" in body["columns"]

def test_upload_no_file(client):
    res = client.post("/api/upload", data={},
                      content_type="multipart/form-data")
    assert res.status_code == 400

def test_upload_wrong_type(client):
    data = {"file": (io.BytesIO(b"hello"), "file.txt")}
    res = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 400

def test_profile_without_upload(client):
    res = client.get("/api/profile")
    assert res.status_code == 400

def test_clean_after_upload(client):
    client.post("/api/upload",
                data = {"file": csv_file()},
                content_type="multipart/form-data")
    res = client.post("/api/clean",
                      json={"drop_duplicate_rows": True, "null_strategy": "fill_median"},)
    assert res.status_code == 200
    body = res.get_json()
    assert "rows_before" in body
    assert "steps" in body

def test_chart_after_upload(client):
    client.post("/api/upload",
                data={"file": csv_file()},
                content_type="multipart/form-data")
    res = client.post("/api/chart",
                      json={"chart_type": "bar", "x": "name", "y":"salary"},
                      content_type="appilcation/json")
    assert res.status_code == 200
    assert "chart" in res.get_json()
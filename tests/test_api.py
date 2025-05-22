import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_document_retrieval_metadata():
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        doc = data[0]
        assert "filename" in doc
        assert "page_count" in doc
        assert "upload_time" in doc

def test_query_handling_after_upload():
    pdf_path = "tests/sample.pdf"
    assert os.path.exists(pdf_path), "sample.pdf not found in tests/"

    with open(pdf_path, "rb") as f:
        upload_response = client.post("/upload", files={"files": ("sample.pdf", f, "application/pdf")})

    print("Upload response JSON:", upload_response.json())

    assert upload_response.status_code == 200
    result = upload_response.json()["results"][0]
    assert result["status"] == "success"

    query_response = client.get("/query", params={"q": "What is this document about?"})
    assert query_response.status_code == 200
    assert isinstance(query_response.text, str)
    assert query_response.text.strip() != ""



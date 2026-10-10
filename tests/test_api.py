from app.app import create_app
from src.preprocessing import FEATURES


SAMPLE = {
    "Gender": "Male",
    "Study_Hours_per_Week": 15,
    "Attendance_Rate": 85,
    "Past_Exam_Scores": 70,
    "Parental_Education_Level": "Bachelor",
    "Internet_Access_at_Home": "Yes",
    "Extracurricular_Activities": "Yes",
}


class StubModel:
    def predict(self, data):
        assert list(data.columns) == FEATURES
        return [1]

    def predict_proba(self, data):
        return [[0.1, 0.9]]


def test_health_and_readiness():
    client = create_app(model=StubModel()).test_client()

    assert client.get("/health").get_json() == {"status": "ok"}
    assert client.get("/ready").get_json() == {"status": "ready"}


def test_form_home_and_prediction():
    client = create_app(model=StubModel()).test_client()

    assert client.get("/").status_code == 200
    response = client.post("/predict", data=SAMPLE)

    assert response.status_code == 200
    assert b"Prediction Result" in response.data
    assert b"Pass" in response.data


def test_predict_get_redirects_to_home():
    client = create_app(model=StubModel()).test_client()

    response = client.get("/predict")

    assert response.status_code == 302
    assert response.location.endswith("/")


def test_predict_returns_label_and_probability():
    client = create_app(model=StubModel()).test_client()

    response = client.post("/predict", json=SAMPLE)

    assert response.status_code == 200
    assert response.get_json() == {
        "prediction": "Pass",
        "probability": {"Fail": 0.1, "Pass": 0.9},
    }


def test_predict_rejects_missing_feature():
    client = create_app(model=StubModel()).test_client()
    payload = dict(SAMPLE)
    payload.pop("Gender")

    response = client.post("/predict", json=payload)

    assert response.status_code == 400
    assert response.get_json()["features"] == ["Gender"]


def test_predict_rejects_unexpected_feature():
    client = create_app(model=StubModel()).test_client()
    payload = dict(SAMPLE, Final_Exam_Score=90)

    response = client.post("/predict", json=payload)

    assert response.status_code == 400
    assert response.get_json()["features"] == ["Final_Exam_Score"]

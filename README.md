# student_performance_mlops

Student performance classification project with a trained scikit-learn pipeline and a Group 1 serving stack.

## What is already done

- Dataset analysis and leakage handling
- Preprocessing pipeline in [`src/preprocessing.py`](./src/preprocessing.py)
- Model training and persistence in [`src/train.py`](./src/train.py)
- Held-out evaluation in [`src/evaluate.py`](./src/evaluate.py)
- Automated tests in [`tests/test_pipeline.py`](./tests/test_pipeline.py)

## Group 1 deliverables

- Flask prediction API in [`app/app.py`](./app/app.py)
- Waitress entrypoint in [`app/wsgi.py`](./app/wsgi.py)
- Docker image via [`Dockerfile`](./Dockerfile)
- Local compose stack via [`docker-compose.yml`](./docker-compose.yml)
- Base Kubernetes manifests in [`k8s/`](./k8s)
- Nginx reverse proxy config in [`nginx/nginx.conf`](./nginx/nginx.conf)

## Run locally

### API

```bash
python -m app.app
```

### Tests

```bash
python -m pytest -q
```

### Docker Compose

```bash
docker compose up --build
```

The API is available through Nginx on port `8080`.
if running via docker use 8080

## API endpoints

- `GET /health`
- `GET /ready`
- `POST /predict`

Example payload:

```json
{
  "Gender": "Male",
  "Study_Hours_per_Week": 15,
  "Attendance_Rate": 85,
  "Past_Exam_Scores": 70,
  "Parental_Education_Level": "Bachelor",
  "Internet_Access_at_Home": "Yes",
  "Extracurricular_Activities": "Yes"
}
```

## Notes

- The API uses [`models/model.pkl`](./models/model.pkl), which already excludes the leaked `Final_Exam_Score` feature.
- Kubernetes manifests are intentionally limited to the base Deployment and Service for Group 1.

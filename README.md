# student_performance_mlops

Student performance classification project with a trained scikit-learn pipeline and a Group 1 serving stack (Flask + Waitress + Docker + Nginx).

The model predicts `Pass_Fail` (`Pass` / `Fail`) from student information.

## What is already done

- Dataset analysis and leakage handling
- Preprocessing pipeline in [`src/preprocessing.py`](src/preprocessing.py)
- Model training and persistence in [`src/train.py`](src/train.py)
- Held-out evaluation in [`src/evaluate.py`](src/evaluate.py)
- Automated tests in [`tests/test_pipeline.py`](tests/test_pipeline.py) and [`tests/test_api.py`](tests/test_api.py)

## Group 1 deliverables

- Flask prediction API in [`app/app.py`](app/app.py)
- Web form templates in [`app/templates/`](app/templates) (`index.html`, `prediction.html`)
- Waitress production server (runs inside the container)
- Docker image via [`Dockerfile`](Dockerfile)
- Local compose stack (Flask + Nginx) via [`docker-compose.yml`](docker-compose.yml)
- Nginx reverse proxy config in [`nginx/nginx.conf`](nginx/nginx.conf)
- Base Kubernetes manifests in [`k8s/`](k8s)

## Architecture

```
Browser -> localhost:8080 -> [nginx :80] -> [flask container :5000, Waitress]
```

- Only Nginx is published to the host (port `8080`).
- The Flask container only uses `expose: 5000`, so it is reachable by Nginx inside the compose network but not directly from the host.
- Nginx finds Flask by its compose service name (`flask`).
- Waitress must listen on `0.0.0.0` (not `127.0.0.1`), otherwise Nginx cannot reach it.

## Run locally

### API (without Docker)

```
python -m app.app
```

### Tests

```
python -m pytest -q
```

### Docker Compose

```
docker compose up --build
```

The API is available through Nginx on port **8080**. When running via Docker, always use `8080` (not `5000`).

To stop the stack:

```
docker compose down
```

## Checking that it is running

Use a second terminal while `docker compose up` is running.

1. Container status (both `flask` and `nginx` should be `Up`, flask `healthy`):

   ```
   docker compose ps
   ```

2. Health and readiness:

   ```
   curl.exe http://localhost:8080/health
   curl.exe http://localhost:8080/ready
   ```

3. Web form: open <http://localhost:8080/>, fill in the student details and submit. The result page shows `Pass` or `Fail`.

4. Prediction API: save the example payload below as `test.json`, then run:

   ```
   curl.exe -X POST http://localhost:8080/predict -H "Content-Type: application/json" -d "@test.json"
   ```

5. Logs:

   ```
   docker compose logs -f flask
   ```

On Windows PowerShell, use `curl.exe` instead of `curl`, because `curl` is an alias for `Invoke-WebRequest`.

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

## Docker notes

- Base image: `python:3.12-slim`.
- The image contains only `app/`, `src/` and `models/`. Data, notebooks, tests and artifacts are not needed at runtime.
- Dependencies are installed from `app/requirements.txt` before the code is copied, so code-only changes rebuild quickly.
- Waitress serves the Flask app on `0.0.0.0:5000` inside the container.
- The container healthcheck calls `/health`.
- `.dockerignore` excludes `.git`, `.venv`, `.pytest_cache`, `**/__pycache__`, `artifacts`, `data`, `notebooks`, `tests`, `k8s`, `nginx` and similar files. Note that `__pycache__` needs the `**/` prefix to match inside subfolders.

### Dependency versions matter

`models/model.pkl` was trained with **scikit-learn 1.7.2**. The same version must be installed in the container (and in your local `.venv`):

```
scikit-learn==1.7.2
```

Using a different version loads the pickle with an `InconsistentVersionWarning` and can fail at prediction time, for example:

```
AttributeError: 'SimpleImputer' object has no attribute '_fill_dtype'
```

If you retrain with `src/train.py`, train in an environment with the same scikit-learn version that is pinned in `app/requirements.txt`.

`app/requirements.txt` must also include `pandas`, which the preprocessing and prediction code needs. Without it the container exits at startup with `No module named 'pandas'`.

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `No module named 'pandas'` (or another package) in the flask logs | The package is missing from `app/requirements.txt`. Add it and rebuild with `docker compose build --no-cache flask`. |
| `502 Bad Gateway` from Nginx | Flask is not reachable. Check that Waitress listens on `0.0.0.0:5000`, that `proxy_pass` uses `http://flask:5000`, and run `docker compose logs flask`. |
| `/predict` returns 500 with a scikit-learn attribute error | scikit-learn version mismatch. Pin `scikit-learn==1.7.2` and rebuild. |
| `InconsistentVersionWarning` at startup | Same cause: the installed scikit-learn version differs from the one used to train the model. |
| `pip install` step shows `CACHED` after editing requirements | You edited the wrong file. The Docker build uses `app/requirements.txt`. |
| Container exits immediately | Run `docker compose logs flask --tail 40` and look for the line starting with `There was an exception ... importing your module`. |

## Notes

- The API uses [`models/model.pkl`](models/model.pkl), which already excludes the leaked `Final_Exam_Score` feature. Do not use `Final_Exam_Score` in the API.
- Kubernetes manifests are intentionally limited to the base Deployment and Service for Group 1.
- When using Kubernetes, the Nginx `proxy_pass` target becomes the Flask Kubernetes Service name instead of the compose service name `flask`.

## Roadmap

- Group 1 (Build, Package, Serve): ML pipeline, tests, Flask API + Waitress, Docker, Nginx, base Kubernetes manifests
- Group 2: Git branching workflow, MLflow, Jenkins CI/CD, Kubernetes HPA/scaling, Prometheus + Grafana, drift detection
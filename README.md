# student_performance_mlops

Student performance classification project with a trained scikit-learn pipeline and a Group 1 serving stack (Flask + Waitress + Docker + Nginx).

The model predicts `Pass_Fail` (`Pass` / `Fail`) from student information.

The repository contains **two serving versions** that can be run side by side:

| Version | Folder | Description | Port |
| --- | --- | --- | --- |
| Single service | `app/` + root `Dockerfile` + root `docker-compose.yml` | One Flask app (UI + model) behind Nginx | 8080 |
| Microservices | `microservices/` | Separate `webapp` (UI + model) and `dbapp` (SQLite storage) behind Nginx | 8081 |

## What is already done

- Dataset analysis and leakage handling
- Preprocessing pipeline in [`src/preprocessing.py`](src/preprocessing.py)
- Model training and persistence in [`src/train.py`](src/train.py)
- Held-out evaluation in [`src/evaluate.py`](src/evaluate.py)
- Automated tests in [`tests/test_pipeline.py`](tests/test_pipeline.py) and [`tests/test_api.py`](tests/test_api.py)

## Group 1 deliverables

- Flask prediction API in [`app/app.py`](app/app.py) (single-service version)
- Microservices version in [`microservices/`](microservices) (webapp + dbapp)
- Waitress production server (runs inside the containers)
- Docker images via the Dockerfiles
- Local compose stacks via `docker-compose.yml` (root) and `microservices/docker-compose.yml`
- Nginx reverse proxy configs: [`nginx/nginx.conf`](nginx/nginx.conf) and [`microservices/nginx.conf`](microservices/nginx.conf)
- Base Kubernetes manifests in [`k8s/`](k8s)

## Project structure

```
student_performance_mlops/
├── app/                      single-service Flask app (templates, requirements)
├── data/                     dataset
├── k8s/                      Kubernetes manifests
├── models/model.pkl          trained pipeline (leakage feature excluded)
├── nginx/nginx.conf          Nginx config for the single-service stack
├── notebooks/
├── src/                      preprocessing, training, evaluation
├── tests/
├── Dockerfile                single-service image
├── docker-compose.yml        single-service stack (Nginx on 8080)
└── microservices/
    ├── docker-compose.yml    webapp + dbapp + Nginx (Nginx on 8081)
    ├── nginx.conf
    ├── webapp/
    │   ├── app.py            UI, model, calls dbapp over HTTP
    │   ├── model.pkl         copy of models/model.pkl
    │   ├── requirements.txt
    │   ├── Dockerfile
    │   └── templates/        index.html, prediction.html, records.html
    └── dbapp/
        ├── app.py            REST API over SQLite
        ├── requirements.txt
        └── Dockerfile
```

## Run locally

### Tests

```
python -m pytest -q
```

### Single-service version

```
docker compose up --build
```

Available through Nginx on port **8080**. Stop with `docker compose down`.

### Microservices version

```
cd microservices
docker compose up --build
```

Available through Nginx on port **8081**. Stop with `docker compose down` (from the `microservices` folder). Use `docker compose down -v` to also delete the database volume.

Before the first build, make sure `microservices/webapp/model.pkl` exists (copy it from `models/model.pkl`):

```
copy models\model.pkl microservices\webapp\model.pkl
```

When running via Docker, always use the Nginx port (8080 or 8081), not the internal ports.

## Microservices architecture

```
Browser -> nginx :8081 -> webapp :5000 --HTTP--> dbapp :8001 -> SQLite file (docker volume /data)
```

- **webapp**: serves the form, validates input, runs the model, shows the result with Pass/Fail and probabilities, and sends each prediction to `dbapp`. It also serves the records page.
- **dbapp**: stores predictions in SQLite and returns them as JSON. It is only reachable inside the compose network.
- **nginx**: the only published service; it forwards everything to `webapp`.
- The webapp keeps working if `dbapp` is down: the prediction is still returned, a warning is logged, and `/show-records` returns a 503 page.
- The SQLite file lives on the named volume `dbdata`, so records survive `docker compose down` and `up`.
- Compose starts the services in order using healthchecks: `dbapp`, then `webapp`, then `nginx`.

## Checking that it is running

Use a second terminal while the stack is up (replace `8081` with `8080` for the single-service version).

1. Container status (all services `Up`, app services `healthy`):

   ```
   docker compose ps
   ```

2. Health and readiness:

   ```
   curl.exe http://localhost:8081/health
   curl.exe http://localhost:8081/ready
   ```

3. Web form: open <http://localhost:8081/>, fill in the details and submit. The result page shows `Pass` or `Fail` plus the Fail and Pass probabilities.

4. Stored records (microservices version): open <http://localhost:8081/show-records>, or use the "View all records" button on the form page.

5. Prediction API: save the example payload below as `test.json`, then run:

   ```
   curl.exe -X POST http://localhost:8081/predict -H "Content-Type: application/json" -d "@test.json"
   ```

6. Logs:

   ```
   docker compose logs -f webapp
   docker compose logs -f dbapp
   ```

7. Persistence check: run `docker compose down`, then `docker compose up`, and confirm the records are still listed.

On Windows PowerShell, use `curl.exe` instead of `curl`, because `curl` is an alias for `Invoke-WebRequest`.

## API endpoints

### webapp (through Nginx)

- `GET /` : prediction form
- `POST /predict` : form submission or JSON
- `GET /show-records` : table of stored predictions (microservices version)
- `GET /health`
- `GET /ready`

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

Example JSON response:

```json
{
  "prediction": "Pass",
  "probability": { "Fail": 0.18, "Pass": 0.82 }
}
```

Missing or non-numeric fields return HTTP 400 with an `error` message.

### dbapp (internal only)

- `POST /add_record` : store one prediction (requires all 7 features and `prediction`)
- `GET /get_records` : list stored predictions, newest first
- `GET /health`

## Model labels

The model was trained on a numeric target (`classes_` is `[0 1]`). The webapp maps `0` to `Fail` and `1` to `Pass`, and stores the text label in the database. If the encoding ever changes, update `LABEL_MAP` in `microservices/webapp/app.py`.

## Docker notes

- Base image: `python:3.12-slim`.
- Single-service image contains `app/`, `src/` and `models/`. Each microservice image contains only its own folder.
- Dependencies are installed before the code is copied, so code-only changes rebuild quickly.
- Waitress serves the apps on `0.0.0.0` inside the containers (5000 for webapp, 8001 for dbapp). Binding to `127.0.0.1` would make them unreachable from Nginx.
- Each container has a healthcheck calling `/health`.
- Templates and the model are copied into the image at build time. Rebuild with `docker compose up --build` after editing them.
- Use `**/__pycache__` (not `__pycache__`) in `.dockerignore`, so nested cache folders are excluded too.

### Dependency versions matter

`models/model.pkl` was trained with **scikit-learn 1.7.2**. The same version must be installed in the containers (and in your local `.venv`):

```
scikit-learn==1.7.2
```

A different version loads the pickle with an `InconsistentVersionWarning` and can fail at prediction time, for example:

```
AttributeError: 'SimpleImputer' object has no attribute '_fill_dtype'
```

If you retrain with `src/train.py`, train in an environment with the same scikit-learn version that is pinned in the requirements files, then copy the new model to `microservices/webapp/model.pkl` as well.

The webapp requirements must also include `pandas`, which the prediction code needs. Without it the container exits at startup with `No module named 'pandas'`.

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `No module named 'pandas'` (or another package) in the logs | Package missing from that service's `requirements.txt`. Add it and rebuild with `docker compose build --no-cache`. |
| Build fails at `COPY requirements.txt` | The service folder has no `requirements.txt`. |
| `502 Bad Gateway` from Nginx | The app container is not reachable. Check the app listens on `0.0.0.0`, that `proxy_pass` uses the right service name (`flask` or `webapp`), and read `docker compose logs`. |
| `/predict` returns 500 with a scikit-learn attribute error | scikit-learn version mismatch. Pin `scikit-learn==1.7.2` and rebuild. |
| `InconsistentVersionWarning` at startup | Same cause as above. |
| Result page shows `1` or `0` instead of Pass/Fail | Old `webapp/app.py` without the label mapping. Rebuild with the current version. |
| Probabilities are not shown | The template needs `probability` from the webapp. Use the current `webapp/app.py`. |
| "Missing field: ..." error | A form input `name` does not match the feature names exactly. |
| `/show-records` returns 503 | `dbapp` is down or unreachable. Check `docker compose logs dbapp`. |
| `pip install` step shows `CACHED` after editing requirements | You edited the wrong file. Each service builds from its own `requirements.txt`. |
| Container exits immediately | Run `docker compose logs <service> --tail 40` and look for the line starting with `There was an exception ... importing your module`. |

## Notes

- The API uses [`models/model.pkl`](models/model.pkl), which already excludes the leaked `Final_Exam_Score` feature. Do not use `Final_Exam_Score` in the API.
- SQLite is fine for a single `dbapp` instance. If you later scale `dbapp` to several replicas, move to a server database such as Postgres, because replicas cannot safely share one SQLite file.
- Kubernetes manifests are currently limited to the base Deployment and Service for the single-service version.

## Roadmap

- Group 1 (Build, Package, Serve): ML pipeline, tests, Flask API + Waitress, Docker, Nginx, microservices split with SQLite storage, base Kubernetes manifests
- Group 2: Git branching workflow, MLflow, Jenkins CI/CD, Kubernetes HPA/scaling, Prometheus + Grafana, drift detection
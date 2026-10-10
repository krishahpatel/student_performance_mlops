---
name: mlops-project-split
description: Divide an MLOps course project (Git, MLflow, Docker, Nginx, Kubernetes, Jenkins CI/CD, Prometheus/Grafana, drift) into two balanced subgroups, with workload classification, ownership boundaries, hand-offs and a timeline. Use when a team must split MLOps tasks fairly or check whether a proposed split is balanced.
---

# MLOps Project Split

Split an MLOps project between two subgroups so effort is roughly 50/50 and neither group is blocked waiting on the other.

## Step 1: Fix the scope first

Ask (or infer from the lesson plan) which of these are in or out. Do not assume.

- Kubernetes: in or out? If out, Docker Compose is the deployment layer.
- Monitoring (Prometheus/Grafana) and drift detection: required or bonus?
- Which lecture is the cut-off (for example, only up to CI/CD with Jenkins)?
- Group sizes (to assign per person afterwards).

Lecture-to-topic mapping (Nirma MLOps 4CS104DE25): Git 5-7, Docker 8-11, Kubernetes 12-14, preprocessing/sklearn pipeline 15-19, Airflow 20-21, cloud/edge 22-24, model versions and A/B 25-26, CI/CD and Jenkins 27-28, tests/retraining 29-31, monitoring/drift 32-36, ethics 37-40, demo 41-45.

## Step 2: Rate every task

Rate each task on setup effort, integration risk and dependency, then give person-days (midpoints).

| Task | Effort (days) | Load |
|---|---|---|
| ML pipeline (preprocess, train, evaluate) | 3-4 | Medium |
| Flask API + Waitress | 1-2 | Light |
| MLflow (server + logging calls) | 1-2 | Light |
| Docker (multi-stage, health checks) | 2-3 | Medium |
| K8s base manifests (Deployment, Service, probes) | 3-4 | Heavy |
| Nginx (reverse proxy, routing) | 1-2 | Light |
| Git workflow (branching, PR rules) | 1 | Light |
| Jenkins CI/CD (lint, test, build, push, deploy) | 4-6 | Heaviest |
| K8s scaling (HPA, limits, rolling updates) | 2-3 | Medium-Heavy |
| Prometheus + Grafana | 3-4 | Medium-Heavy |
| Drift detection (simple version) | 2 | Medium |
| Pytest tests (feed Jenkins) | 1-2 | Light |

Tiers: **Light** = a few files, little to break. **Medium** = a real tool setup with a few moving parts. **Heavy** = several tools must talk to each other (Jenkins -> registry -> Kubernetes, HPA with metrics).

## Step 3: Assign using these rules

1. **Theme each group.** Group 1 = build, package, serve (the request path). Group 2 = automate, deploy, observe (everything that watches or ships the app).
2. **One group owns the whole request path** (Nginx -> Waitress -> Flask -> model) so it can be built and debugged end to end.
3. **MLflow:** the logging calls live in the training script, so the training owner (Group 1) owns them. The server is one container (SQLite backend, local artifact volume), so it is light and goes with the same owner.
4. **Kubernetes:** split by level, not by tool. Group 1 writes base manifests (Pods, Deployment, Service, probes). Group 2 adds HPA, resource limits and rolling updates, through pull requests in the same `k8s/` folder.
5. **Nginx and K8s Service both load balance.** Give Nginx one clear role (standalone reverse proxy, or Ingress) so traffic management is not done twice.
6. **Prometheus:** Group 1 adds `/metrics` to Flask (about 10 lines). Group 2 writes `prometheus.yml` and the dashboards.
7. **Tests:** the group that writes the code writes its pytest tests. Jenkins runs them as a gate.
8. **Git/DVC:** versioning of code and data is separate from MLflow, which versions experiments and models.
9. **Rebalance with small movable tasks:** pytest (1.5 days) and drift (2 days) can move between groups without changing the architecture.

## Step 4: Compute the percentages

Show both numbers:

- **Raw share:** sum midpoint days per group, divide by the total.
- **Risk-adjusted share:** add about 30% to the heavy integration tasks (Jenkins, K8s scaling, Prometheus/Grafana) before dividing.

Aim for within about 5 points of 50/50 on the risk-adjusted figure. If not, move pytest or drift.

## Step 5: Reference split (K8s in, monitoring in)

| Group 1: Build, package, serve | Group 2: Automate, deploy, observe |
|---|---|
| ML pipeline | Git workflow (branching, PR rules, webhook) |
| MLflow (server, tracking, registry) | Jenkins CI/CD (lint, test, build, push, deploy) |
| Flask API + Waitress | K8s scaling (HPA, limits, rolling updates) |
| Docker (multi-stage, health checks) | Prometheus + Grafana |
| K8s base manifests | Drift detection (simple version) |
| Nginx | |

Approximate result: 52/48 raw, 47/53 risk-adjusted. Moving drift to Group 1 gives about 51/49.

If Kubernetes is out: drop both K8s rows, use Docker Compose as the deployment layer, and move Airflow (Lectures 20-21) to Group 1 to keep the split even. A/B testing becomes two model containers behind Nginx.

## Step 6: Hand-offs and day-1 agreements

Agree these before anyone starts:

- `/predict` input schema (the dataset's features)
- Docker image name and tag convention
- Service names (`flask`, `nginx`, `mlflow`, `prometheus`, `grafana`, `jenkins`)
- MLflow tracking URI (`http://mlflow:5000`)
- Repo layout, so Jenkins knows where tests, Dockerfile and manifests are
- One `docker-compose.yml` owned by Group 1; Group 2 adds its services

Group 1 pushes a stub `/predict` Flask app and Dockerfile on day 1 so Group 2 can start.

## Step 7: Timeline (about 6 weeks)

- **Weeks 1-2:** Group 1 builds data, model, Flask, Dockerfile. Group 2 sets up Git, the Jenkins skeleton and Prometheus on a dummy app.
- **Weeks 3-4:** Group 1 delivers K8s base manifests, Nginx and MLflow logging. Group 2 plugs the real repo into Jenkins and adds scaling.
- **Weeks 5-6:** Group 2 builds Grafana dashboards and drift. Group 1 polishes the model and fixes bugs. Both integrate and prepare the demo.

## Risks to warn about

- **Jenkins deploying to Kubernetes** needs kubectl and a kubeconfig reachable from inside the Jenkins container. Treat "build and push image" as the guaranteed finish line and the K8s deploy as a stretch step.
- **Laptop RAM:** minikube plus Jenkins plus Grafana is heavy. Fall back to Docker Compose if needed.
- **Group 2 is back-loaded** (needs a running app). Give it dummy-app work early.
- **Do not claim syllabus coverage** (retraining, cloud deployment, bias/fairness) unless a task list actually includes it; otherwise mark it as report-only.

## Output format

Give: the two-group table, the workload table, raw and risk-adjusted percentages, hand-offs, timeline, and risks. Offer a per-person breakdown once group sizes are known.

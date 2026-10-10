import os
import pickle
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, redirect, render_template, request, url_for
import waitress

from src.preprocessing import FEATURES

app = Flask(__name__)

# Load the trained preprocessing and prediction pipeline
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = Path(
    os.environ.get("MODEL_PATH", str(PROJECT_ROOT / "models" / "model.pkl"))
)

with MODEL_PATH.open("rb") as model_file:
    model = pickle.load(model_file)


@app.route('/')
def welcome():
    return render_template("index.html", features=FEATURES)


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


@app.route('/ready')
def ready():
    return jsonify({"status": "ready"})


@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'GET':
        return redirect(url_for('welcome'))

    is_json_request = request.is_json

    payload = (
        request.get_json(silent=True)
        if is_json_request
        else request.form.to_dict()
    )

    if not isinstance(payload, dict):
        error = "Request body must be a JSON object"
        return jsonify({"error": error}), 400

    if not is_json_request:
        try:
            for feature in (
                "Study_Hours_per_Week",
                "Attendance_Rate",
                "Past_Exam_Scores"
            ):
                payload[feature] = float(payload[feature])

        except (KeyError, TypeError, ValueError):
            return render_template(
                "index.html",
                features=FEATURES,
                error="Study hours, attendance, and past exam scores must be numbers.",
                form_data=payload,
            ), 400

    missing_features = [
        feature for feature in FEATURES if feature not in payload
    ]

    if missing_features:
        error = {
            "error": "Missing required features",
            "features": missing_features
        }

        if not is_json_request:
            return render_template(
                "index.html",
                features=FEATURES,
                error=f"Missing required features: {', '.join(missing_features)}",
                form_data=payload,
            ), 400

        return jsonify(error), 400

    unexpected_features = sorted(set(payload) - set(FEATURES))

    if unexpected_features:
        error = {
            "error": "Unexpected features",
            "features": unexpected_features
        }

        if not is_json_request:
            return render_template(
                "index.html",
                features=FEATURES,
                error=f"Unexpected features: {', '.join(unexpected_features)}",
                form_data=payload,
            ), 400

        return jsonify(error), 400

    input_data = pd.DataFrame(
        [{feature: payload[feature] for feature in FEATURES}],
        columns=FEATURES,
    )

    prediction = model.predict(input_data)[0]

    label = {0: "Fail", 1: "Pass"}.get(int(prediction))

    if label is None:
        return jsonify({
            "error": "Model returned an unsupported prediction"
        }), 500

    response = {"prediction": label}

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(input_data)[0]

        response["probability"] = {
            "Fail": float(probabilities[0]),
            "Pass": float(probabilities[1]),
        }

    if not is_json_request:
        return render_template(
            "prediction.html",
            prediction=response["prediction"],
            probability=response.get("probability"),
        )

    return jsonify(response)


if __name__ == "__main__":
    waitress.serve(
        app=app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000"))
    )
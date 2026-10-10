import os
import pickle
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, redirect, render_template, request, url_for

from src.preprocessing import FEATURES


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = Path(
    os.environ.get("MODEL_PATH", str(PROJECT_ROOT / "models" / "model.pkl"))
)


def load_model(model_path=MODEL_PATH):
    """Load the trained preprocessing and prediction pipeline."""
    with model_path.open("rb") as model_file:
        return pickle.load(model_file)


def create_app(model=None):
    app = Flask(__name__)
    prediction_model = model if model is not None else load_model()

    @app.get("/")
    def welcome():
        return render_template("index.html", features=FEATURES)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/ready")
    def ready():
        return jsonify({"status": "ready"})

    @app.route("/predict", methods=["GET", "POST"])
    def predict():
        if request.method == "GET":
            return redirect(url_for("welcome"))

        is_json_request = request.is_json
        payload = request.get_json(silent=True) if is_json_request else request.form.to_dict()
        if not isinstance(payload, dict):
            error = "Request body must be a JSON object"
            return jsonify({"error": error}), 400

        if not is_json_request:
            try:
                for feature in ("Study_Hours_per_Week", "Attendance_Rate", "Past_Exam_Scores"):
                    payload[feature] = float(payload[feature])
            except (KeyError, TypeError, ValueError):
                return render_template(
                    "index.html",
                    features=FEATURES,
                    error="Study hours, attendance, and past exam scores must be numbers.",
                    form_data=payload,
                ), 400

        missing_features = [feature for feature in FEATURES if feature not in payload]
        if missing_features:
            error = {"error": "Missing required features", "features": missing_features}
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
            error = {"error": "Unexpected features", "features": unexpected_features}
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
        prediction = prediction_model.predict(input_data)[0]
        label = {0: "Fail", 1: "Pass"}.get(int(prediction))
        if label is None:
            return jsonify({"error": "Model returned an unsupported prediction"}), 500

        response = {"prediction": label}
        if hasattr(prediction_model, "predict_proba"):
            probabilities = prediction_model.predict_proba(input_data)[0]
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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))

import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Absolute path so it can live on a docker volume (mounted at /data).
db_path = os.environ.get("DATABASE_PATH", "/data/student_predictions.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

REQUIRED_FIELDS = [
    "Gender",
    "Study_Hours_per_Week",
    "Attendance_Rate",
    "Past_Exam_Scores",
    "Parental_Education_Level",
    "Internet_Access_at_Home",
    "Extracurricular_Activities",
    "prediction",
]


class Prediction(db.Model):
    __tablename__ = "prediction"

    id = db.Column(db.Integer, primary_key=True)
    Gender = db.Column(db.String(20))
    Study_Hours_per_Week = db.Column(db.Float)
    Attendance_Rate = db.Column(db.Float)
    Past_Exam_Scores = db.Column(db.Float)
    Parental_Education_Level = db.Column(db.String(50))
    Internet_Access_at_Home = db.Column(db.String(10))
    Extracurricular_Activities = db.Column(db.String(10))
    prediction = db.Column(db.String(50))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )


# Create tables at import time so it also works under waitress
# (not only when run with `python app.py`).
with app.app_context():
    db.create_all()


@app.route("/add_record", methods=["POST"])
def add_record():
    data = request.get_json(silent=True) or {}

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Only accept known fields instead of blindly unpacking the payload.
    record = Prediction(**{f: data[f] for f in REQUIRED_FIELDS})
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "Record added successfully"}), 201


@app.route("/get_records", methods=["GET"])
def get_records():
    records = Prediction.query.order_by(Prediction.id.desc()).all()
    return jsonify(
        [
            {
                "id": r.id,
                "Gender": r.Gender,
                "Study_Hours_per_Week": r.Study_Hours_per_Week,
                "Attendance_Rate": r.Attendance_Rate,
                "Past_Exam_Scores": r.Past_Exam_Scores,
                "Parental_Education_Level": r.Parental_Education_Level,
                "Internet_Access_at_Home": r.Internet_Access_at_Home,
                "Extracurricular_Activities": r.Extracurricular_Activities,
                "prediction": r.prediction,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)

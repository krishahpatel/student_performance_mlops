import json
import os
import pickle

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.preprocessing import FEATURES, TARGET, create_preprocessor, load_data


DATA_PATH = "data/student_performance_dataset.csv"
MODEL_PATH = "models/model.pkl"
TEST_DATA_PATH = "artifacts/test_data.csv"
METRICS_PATH = "artifacts/metrics.json"


def main():
    df = load_data(DATA_PATH)

    X = df[FEATURES]
    y = df[TARGET].map({"Fail": 0, "Pass": 1})

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            random_state=42,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            random_state=42,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            random_state=42,
        ),
    }

    results = {}
    trained_pipelines = {}

    for name, model in models.items():
        pipeline = Pipeline([
            ("preprocessor", create_preprocessor()),
            ("model", model),
        ])

        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred),
        }

        results[name] = metrics
        trained_pipelines[name] = pipeline

        print(f"\n{name}")
        print("-" * len(name))

        for metric, value in metrics.items():
            print(f"{metric}: {value:.4f}")

    best_name = max(
        results,
        key=lambda name: results[name]["f1"]
    )

    print(f"\nBest model: {best_name}")

    best_pipeline = trained_pipelines[best_name]

    os.makedirs("models", exist_ok=True)
    os.makedirs("artifacts", exist_ok=True)

    # Save the trained pipeline
    with open(MODEL_PATH, "wb") as file:
        pickle.dump(best_pipeline, file)

    # Save the held-out test set
    test_data = X_test.copy()
    test_data[TARGET] = y_test.values
    test_data.to_csv(TEST_DATA_PATH, index=False)

    # Save model metrics
    output = {
        "best_model": best_name,
        "metrics": results,
    }

    with open(METRICS_PATH, "w") as file:
        json.dump(output, file, indent=4)

    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Test data saved to: {TEST_DATA_PATH}")
    print(f"Metrics saved to: {METRICS_PATH}")


if __name__ == "__main__":
    main()
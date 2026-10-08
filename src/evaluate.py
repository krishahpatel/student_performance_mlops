import json
import pickle

import matplotlib.pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    classification_report,
    confusion_matrix,
)

from src.preprocessing import FEATURES, TARGET


MODEL_PATH = "models/model.pkl"
TEST_DATA_PATH = "artifacts/test_data.csv"


def main():
    with open(MODEL_PATH, "rb") as file:
        model = pickle.load(file)

    with open(TEST_DATA_PATH, "r") as file:
        import pandas as pd
        test_data = pd.read_csv(file)

    X_test = test_data[FEATURES]
    y_test = test_data[TARGET]

    y_pred = model.predict(X_test)

    print("Classification Report")
    print("=====================")

    print(
        classification_report(
            y_test,
            y_pred,
            target_names=["Fail", "Pass"],
        )
    )

    cm = confusion_matrix(y_test, y_pred)

    print("Confusion Matrix")
    print("================")
    print(cm)

    ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Fail", "Pass"],
    ).plot()

    plt.title("Student Performance - Test Set")
    plt.tight_layout()

    plt.savefig("artifacts/confusion_matrix.png")
    plt.show()


if __name__ == "__main__":
    main()
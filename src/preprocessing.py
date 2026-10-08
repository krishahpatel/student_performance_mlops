import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer


FEATURES = [
    "Gender",
    "Study_Hours_per_Week",
    "Attendance_Rate",
    "Past_Exam_Scores",
    "Parental_Education_Level",
    "Internet_Access_at_Home",
    "Extracurricular_Activities",
]

TARGET = "Pass_Fail"

LEAKY_COLS = [
    "Student_ID",
    "Final_Exam_Score",
]

NUMERICAL_FEATURES = [
    "Study_Hours_per_Week",
    "Attendance_Rate",
    "Past_Exam_Scores",
]

CATEGORICAL_FEATURES = [
    "Gender",
    "Parental_Education_Level",
    "Internet_Access_at_Home",
    "Extracurricular_Activities",
]


def load_data(path):
    return pd.read_csv(path)


def create_preprocessor():
    numerical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocessor = ColumnTransformer([
        ("numerical", numerical_pipeline, NUMERICAL_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
    ])

    return preprocessor
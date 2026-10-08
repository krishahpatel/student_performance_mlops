import pandas as pd

from src.preprocessing import (
    CATEGORICAL_FEATURES,
    FEATURES,
    LEAKY_COLS,
    NUMERICAL_FEATURES,
    TARGET,
    create_preprocessor,
    load_data,
)


DATA_PATH = "data/student_performance_dataset.csv"


def test_data_loads():
    df = load_data(DATA_PATH)

    assert len(df) == 708
    assert TARGET in df.columns


def test_target_values():
    df = load_data(DATA_PATH)

    assert set(df[TARGET].unique()) == {"Pass", "Fail"}


def test_no_leakage():
    assert TARGET not in FEATURES
    assert not set(LEAKY_COLS) & set(FEATURES)


def test_feature_columns():
    assert len(FEATURES) == 7
    assert len(NUMERICAL_FEATURES) == 3
    assert len(CATEGORICAL_FEATURES) == 4


def test_preprocessor():
    df = load_data(DATA_PATH)

    preprocessor = create_preprocessor()

    transformed = preprocessor.fit_transform(df[FEATURES])

    assert transformed.shape[0] == len(df)
    assert transformed.shape[1] > len(FEATURES)


def test_preprocessor_handles_unseen_category():
    df = load_data(DATA_PATH)

    preprocessor = create_preprocessor()
    preprocessor.fit(df[FEATURES])

    sample = df[FEATURES].iloc[[0]].copy()

    sample["Gender"] = "Unknown"

    transformed = preprocessor.transform(sample)

    assert transformed.shape[0] == 1
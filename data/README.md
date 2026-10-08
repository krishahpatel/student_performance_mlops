# Data

The dataset is not stored in Git (`data/*.csv` is ignored).

1. Download it from Kaggle: https://www.kaggle.com/datasets/amrmaree/student-performance-prediction
2. Save the CSV as `data/student_performance_dataset.csv`.
3. Train with `python -m src.train` from the project root.

Tests and CI use `tests/sample.csv` (20 rows), so they don't need the full dataset.


import pandas as pd
df = pd.read_csv("../data/student_performance_dataset.csv")
print(df.shape)
print(df.dtypes)
print(df.isna().sum())
print(df.describe(include="all").T)
print(df.head())
import get_data

df = get_data.main(load_from_cache=False, sample=5)
df = get_data.score(df)
print(df.head())
df.to_csv("./output/data.csv", index=False)
df.to_parquet(
    "./output/data.parquet", index=False, engine="pyarrow", compression="gzip"
)
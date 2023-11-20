import get_data


def main():
    df = get_data.load_df(load_from_cache=False, sample=4)
    df = get_data.get_sense_scores(df["text"].values, df["file"].values)
    df.to_csv("./output/data.csv", index=False)


if __name__ == "__main__":
    main()

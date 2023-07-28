import json
import os

import docx
import openai
import pandas as pd
from dotenv import load_dotenv
from nltk.tokenize import sent_tokenize
from retry import retry
from tqdm import tqdm
from transformers import pipeline

load_dotenv()


openai.api_key = os.getenv("OPENAI_KEY")

classify = pipeline(
    task="text-classification",
    model="cffl/bert-base-styleclassification-subjective-neutral",
    return_all_scores=True,
)


def get_text_from_docx(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return "\n".join(fullText)


@retry(Exception, tries=3, delay=5, backoff=2, max_delay=60)
def get_gpt_4_score(t):
    prompt = f"""I am a shareholder.  I am trying to determine the score of a letter from a company to its shareholders in terms of ""sensebreaking"" vs ""sensegiving"", where neutral is the midpoint.
I need a score for each sentence of the letter, on a scale from -1 (sensebreaking) to 1 (sensegiving), with a precision of 0.1. Use a continuous scale of -1 (full sensebreaking) to 1 (full sensegiving). Sensegiving is subjective, oriented toward the future and has a positive tone. Sensebreaking is subjective, oriented toward the past, and has an emotionally negative tone. When the sentence looks fully neutral, assign zero. Here are a few examples of scoring sentences:

Text: I see [the organizational transformation] as a very beneficial development. 
Score: 1

Text: We are back to being errand boys to the Ministry.
Score: -1

Text: Over the past five years, we have reinvested more than$1.6 billion in our business  
Score: 0

Text: What we have now is a really old-school bureaucracy.
Score: -1

Text: This year, we celebrate our 40th anniversary.
Score: 0

Text: The work conducted during the merger preparation will come in handy as we develop the Office.
Score: 1

Text: The Office should never have been founded in the first place
Score: -1

Text: You will find our performance numbers elsewhere in this report. 
Score: 0

Text: I at least am confident about the future, as this [merger] gives us the opportunity to retain our organizational culture.
Score: 1

Text: Let us continue to look at the future with curiosity and resolve.
Score: 1

Text: Since the merger was first hinted at, the Office personnel has had to live with a noose around their necks, uncertain about when they finally open the hatch and let them hang.
Score: -1

Text: [The merger]came to nothing and we needed to return to the old way.
Score: -1

Text: Japan, 30 years ago, was our first international market.  
Score: 0

Text: We welcomed three new members to our Board of Directors this year. 
Score: 0

Text: It was made perfectly clear that the Office personnel stand united, willing to participate in the planning of our future together.
Score: 1

Text: {t.strip()}
Score:"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    scores = response["choices"][0]["message"]["content"]
    return scores


def median(list_values):
    list_values.sort()
    if len(list_values) % 2 == 0:
        return (
            list_values[len(list_values) // 2 - 1] + list_values[len(list_values) // 2]
        ) / 2
    else:
        return list_values[len(list_values) // 2]


def average(list_values):
    return sum(list_values) / len(list_values)


def get_bert_sentiment(corpus, file_names):
    scores = []
    for document, file_name in tqdm(zip(corpus, file_names)):
        sentences = sent_tokenize(document)

        list_scores = classify(sentences, truncation=True)
        transformed_list_scores = []
        sentence_score_map = {}
        for i, score in enumerate(list_scores):
            new_score_d = {}

            for d in score:
                new_score_d[d["label"]] = d["score"]
            transformed_list_scores.append(new_score_d)
            sentence_score_map[sentences[i]] = new_score_d

        scores.append(
            {
                "MEDIAN_SUBJECTIVE": median(
                    [x["SUBJECTIVE"] for x in transformed_list_scores]
                ),
                "MEDIAN_NEUTRAL": median(
                    [x["NEUTRAL"] for x in transformed_list_scores]
                ),
                "AVG_SUBJECTIVE": average(
                    [x["SUBJECTIVE"] for x in transformed_list_scores]
                ),
                "AVG_NEUTRAL": average([x["NEUTRAL"] for x in transformed_list_scores]),
            }
        )
        with open(f"./output/{file_name.split('.doc')[0]}_bert.json", mode="w") as f:
            json.dump(sentence_score_map, f)
    return scores


def get_gpt_sentiment(corpus, file_names):
    scores = []
    for document, file_name in tqdm(zip(corpus, file_names)):
        sentences = sent_tokenize(document)
        sentence_score_map = {}
        fail_ct = 0
        for sent in sentences:
            score = get_gpt_4_score(sent)
            try:
                score = float(score)
                sentence_score_map[sent] = score
            except:
                print("GPT parsing failed")
                sentence_score_map[sent] = 0
                fail_ct += 1
        print("Fail:", fail_ct)
        print("Total:", len(sentence_score_map))
        scores.append(
            {
                "MEDIAN_SCORE": median(list(sentence_score_map.values())),
                "AVG_SCORE": average(list(sentence_score_map.values())),
            }
        )
        with open(f"./output/{file_name.split('.doc')[0]}_gpt.json", mode="w") as f:
            json.dump(sentence_score_map, f)
    return scores


def score(df):
    df["bert_neutral"] = get_bert_sentiment(df["text"].values, df["file"].values)
    # df["gpt_scores"] = get_gpt_sentiment(df["text"].values, df["file"].values)
    return df


def parse_firm_id(file_name):
    file_array = file_name.split("_")
    if len(file_array[0]) == 2:
        return int(file_array[0])
    else:
        return int(file_array[1])


def main(load_from_cache=False, sample=-1):
    if load_from_cache:
        df = pd.read_parquet("./output/data.parquet")
        return df

    data = []
    for root, _, files in os.walk("data"):
        for file in files:
            if not file.endswith(".docx"):
                continue

            data_dict = {
                "path": os.path.join(root, file),
                "file": file,
                "text": get_text_from_docx(os.path.join(root, file)),
            }
            data_dict["firm_type"] = (
                "non_family_firm" if "NFF" in file else "family_firm"
            )

            data_dict["firm_id"] = parse_firm_id(file)

            data.append(data_dict)

    df = pd.DataFrame(data)

    if sample > 0 and sample < len(df):
        sample_id = int(sample / 2)
        df = df[df["firm_id"] <= sample_id]

    df.sort_values(by="firm_id", inplace=True)

    return df

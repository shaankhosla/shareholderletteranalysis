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
    prompt = f"""I'm trying to determine if a letter from a company to its shareholders is "sensebreaking" or "sensegiving". Below is a letter from a company to its shareholders. Score the letter on a scale from -1 (sensebreaking) to 1 (sensegiving). Only output the numerical score from a scale of -1 to 1, no other values or text. Here are a few examples.

    Text:
    The year 2003 was not lacking in drama. . . . The work conducted during the merger preparation did not go to waste, however. It will come in handy as we develop the Office. 
    Score: 1

    Text: Since the merger was first hinted at, the Office personnel has had to live with a noose around their necks, uncertain about when they finally open the hatch and let them hang.
    Score: -1
    
    Text:
    Even though the information session did not offer much new information about the forthcoming merger,
it was made perfectly clear that the Office personnel stand united, willing to participate in the planning of our future together
    Score: 1

    Text: We are back to being errand boys to the Ministry.
    Score: -1

    Text: {t}
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


def get_bert_sentiment(corpus):
    scores = []
    for document in tqdm(corpus):
        sentences = sent_tokenize(document)

        list_scores = classify(sentences, truncation=True)
        transformed_list_scores = []
        for score in list_scores:
            new_score_d = {}

            for d in score:
                new_score_d[d["label"]] = d["score"]
            transformed_list_scores.append(new_score_d)

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
    return scores


def get_gpt_sentiment(corpus):
    scores = []
    for document in tqdm(corpus):
        sentences = sent_tokenize(document)
        list_scores = []
        fail_ct = 0
        for sent in sentences:
            score = get_gpt_4_score(sent)
            try:
                score = float(score)
                list_scores.append(score)
            except:
                print("GPT parsing failed")
                list_scores.append(0)
                fail_ct += 1
        print("Fail:", fail_ct)
        print("Total:", len(list_scores))
        scores.append(
            {
                "MEDIAN_SCORE": median(list_scores),
                "AVG_SCORE": average(list_scores),
            }
        )
    return scores


def score(df):
    df["bert_neutral"] = get_bert_sentiment(df["text"].values)
    df["gpt_scores"] = get_gpt_sentiment(df["text"].values)
    return df


def main(load_from_cache=False, sample=-1):
    if load_from_cache:
        df = pd.read_parquet("./output/data.parquet")
        return df

    data = []
    for root, _, files in os.walk("data"):
        for file in files:
            if file.endswith(".docx"):
                data_dict = {
                    "file": os.path.join(root, file),
                    "text": get_text_from_docx(os.path.join(root, file)),
                }
                if "NFF" in file:
                    data_dict["firm_type"] = "non_family_firm"
                elif "FF" in file:
                    data_dict["firm_type"] = "family_firm"
                else:
                    data_dict["firm_type"] = "other"
                    print("Found other firm type")

                data.append(data_dict)

    df = pd.DataFrame(data)
    if sample > 0 and sample < len(df):
        df = df.sample(n=sample)
    return df

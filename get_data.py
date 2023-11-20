import os

import docx  # type: ignore
import openai  # type: ignore
import pandas as pd  # type: ignore
from dotenv import load_dotenv  # type: ignore
from nltk.tokenize import sent_tokenize  # type: ignore
from retry import retry  # type: ignore
from tqdm import tqdm  # type: ignore
from transformers import pipeline

from prompts import emotion, reframing, stakeholder, subective, visionary

load_dotenv()


openai.api_key = os.getenv("OPENAI_KEY")

subjective_classify = pipeline(
    task="text-classification",
    model="cffl/bert-base-styleclassification-subjective-neutral",
    return_all_scores=True,
)
emotion_classify = pipeline(
    "text-classification",
    model="bhadresh-savani/distilbert-base-uncased-emotion",
    return_all_scores=True,
)


def get_text_from_docx(filename: str) -> str:
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return "\n".join(fullText)


@retry(Exception, tries=3, delay=5, backoff=2, max_delay=60)
def get_gpt_4_score(prompt: str, sentence: str) -> str:
    prompt_to_send = prompt + sentence
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt_to_send}],
    )
    scores = response["choices"][0]["message"]["content"]
    return scores


def median(list_values: list[float]) -> float:
    list_values.sort()
    if len(list_values) % 2 == 0:
        return (
            list_values[len(list_values) // 2 - 1] + list_values[len(list_values) // 2]
        ) / 2
    else:
        return list_values[len(list_values) // 2]


def average(list_values: list[float]) -> float:
    return sum(list_values) / len(list_values)


def get_sense_scores(corpus: list[str], file_names: list[str]) -> pd.DataFrame:
    df = []
    for document, file_name in tqdm(
        zip(corpus, file_names),
        total=len(corpus),
        desc="Getting scores",
    ):
        # convert document to sentences
        sentences = sent_tokenize(document)

        # get all bert scores
        bert_subjective_scores = subjective_classify(sentences, truncation=True)
        bert_emotion_scores = emotion_classify(sentences, truncation=True)

        for i, sent in enumerate(sentences):
            sentence_score_map = {
                "sentence": sent,
                "file": file_name,
            }

            # get score from bert subjective
            for d in bert_subjective_scores[i]:
                sentence_score_map[d["label"] + "_bert"] = d["score"]

            # get score from bert emotion
            for d in bert_emotion_scores[i]:
                sentence_score_map[d["label"] + "_bert"] = d["score"]

            sentence_score_map["emotion_gpt"] = get_gpt_4_score(emotion, sent)
            sentence_score_map["stakeholder_gpt"] = get_gpt_4_score(stakeholder, sent)
            sentence_score_map["reframing_gpt"] = get_gpt_4_score(reframing, sent)
            sentence_score_map["vision_gpt"] = get_gpt_4_score(visionary, sent)
            sentence_score_map["subjective_gpt"] = get_gpt_4_score(subective, sent)

            df.append(sentence_score_map)
    df = pd.DataFrame(df)
    return df


def parse_firm_id(file_name: str) -> int:
    file_array = file_name.split("_")
    if len(file_array[0]) == 2:
        return int(file_array[0])
    else:
        return int(file_array[1])


def load_df(load_from_cache: bool = False, sample: int = -1) -> pd.DataFrame:
    if load_from_cache:
        df = pd.read_parquet("./output/data.parquet")
        return df

    data = []
    for root, _, files in os.walk("data"):
        for file in files:
            if not file.endswith(".docx"):
                continue

            data_dict: dict[str, str | int] = {
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

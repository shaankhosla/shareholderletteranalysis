import os

import docx  # type: ignore
import openai  # type: ignore
import pandas as pd  # type: ignore
from dotenv import load_dotenv  # type: ignore
from nltk.tokenize import sent_tokenize  # type: ignore
from retry import retry  # type: ignore
from tqdm import tqdm  # type: ignore
from transformers import pipeline

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
def get_gpt_4_score(t: str) -> str:
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
    for document, file_name in tqdm(zip(corpus, file_names)):
        # convert document to sentences
        sentences = sent_tokenize(document)

        # get all bert scores
        bert_subjective_scores = subjective_classify(sentences, truncation=True)
        bert_emotion_scores = emotion_classify(sentences, truncation=True)

        for i, sentence in enumerate(sentences):
            sentence_score_map = {
                "sentence": sentence,
                "file": file_name,
            }

            # get score from bert subjective
            for d in bert_subjective_scores[i]:
                sentence_score_map[d["label"] + "_bert"] = d["score"]

            # get score from bert emotion
            for d in bert_emotion_scores[i]:
                sentence_score_map[d["label"] + "_bert"] = d["score"]

            # try to get score from GPT-4
            gpt_score = get_gpt_4_score(sentence)
            try:
                gpt_score = float(gpt_score)
            except:
                gpt_score = None
                print("GPT parsing failed")
            sentence_score_map["gpt_score"] = gpt_score

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

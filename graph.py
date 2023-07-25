import matplotlib.pyplot as plt


def average(list_values):
    return sum(list_values) / len(list_values)


def median(list_values):
    list_values.sort()
    if len(list_values) % 2 == 0:
        return (
            list_values[len(list_values) // 2 - 1] + list_values[len(list_values) // 2]
        ) / 2
    else:
        return list_values[len(list_values) // 2]


def distribution_plot(dict_emotion_list_scores, title, ct):

    emotions = list(dict_emotion_list_scores.keys())
    average_emotion_scores = [
        average(dict_emotion_list_scores[emotion]) for emotion in emotions
    ]

    plt.figure()
    plt.barh(emotions, average_emotion_scores)
    plt.title(title + f" {ct} companies")
    for index, value in enumerate(average_emotion_scores):
        plt.text(value, index, f"{value:.2f}")

    plt.xlabel("Average confidence output")
    plt.savefig(f"./output/{title} Average.png")

    median_emotion_scores = [
        median(dict_emotion_list_scores[emotion]) for emotion in emotions
    ]
    plt.figure()
    plt.barh(emotions, median_emotion_scores)
    plt.title(title + f" {ct} companies")
    for index, value in enumerate(median_emotion_scores):
        plt.text(value, index, f"{value:.2f}")
    plt.xlabel("Median confidence output")
    plt.savefig(f"./output/{title} Median.png")

from hmac import new
from typing import List, Union

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
from bson import ObjectId
from db import DB


def get_scores_for_task_definition(task_definition):
    results = DB.evaluation_scores.find()

    pipeline = [
        {"$addFields": {"benchmark_id": {"$toObjectId": "$benchmark_id"}}},
        {
            "$lookup": {
                "from": "benchmarks",  # the name of the benchmark collection
                "localField": "benchmark_id",  # the field in the evaluation_scores collection
                "foreignField": "_id",  # the field in the benchmark collection
                "as": "benchmark_data",  # the name for the resulting array
            }
        },
        {
            "$unwind": "$benchmark_data"  # deconstructs the array from the previous stage
        },
        {"$match": {"benchmark_data.task_definition": task_definition}},
        {
            "$project": {
                "_id": 0,  # exclude the _id field
                "percentage_score": 1,  # include the overall_score field
                "model": "$benchmark_data.model_params.model",
                "temperature": "$benchmark_data.model_params.temperature",
            }
        },
    ]

    results = DB.evaluation_scores.aggregate(pipeline)
    # print(list(results))
    return list(results)


def get_scores_for_test_run(test_run_id: Union[str, ObjectId]):
    results = DB.evaluation_scores.find({"test_run_id": ObjectId(test_run_id)})

    pipeline = [
        {"$addFields": {"benchmark_id": {"$toObjectId": "$benchmark_id"}}},
        {
            "$lookup": {
                "from": "benchmarks",  # the name of the benchmark collection
                "localField": "benchmark_id",  # the field in the evaluation_scores collection
                "foreignField": "_id",  # the field in the benchmark collection
                "as": "benchmark_data",  # the name for the resulting array
            }
        },
        {
            "$unwind": "$benchmark_data"  # deconstructs the array from the previous stage
        },
        # {"$match": {"benchmark_data.test_run_id": test_run_id}},
        {
            "$project": {
                "_id": 0,  # exclude the _id field
                "percentage_score": 1,  # include the overall_score field
                "model": "$benchmark_data.model_params.model",
                "temperature": "$benchmark_data.model_params.temperature",
                "test_run_id": "$benchmark_data.test_run_id",
            }
        },
    ]

    results = DB.evaluation_scores.aggregate(pipeline)
    # print(list(results))
    return list(results)


def get_scores_for_test_runs(test_run_ids: List[Union[str, ObjectId]]):
    new_test_run_ids = []
    for id in test_run_ids:
        if not isinstance(id, ObjectId):
            new_test_run_ids.append(ObjectId(id))
        else:
            new_test_run_ids.append(id)
    results = DB.evaluation_scores.find({"test_run_id": {"$in": new_test_run_ids}})

    pipeline = [
        {
            "$lookup": {
                "from": "benchmarks",  # the name of the benchmark collection
                "localField": "benchmark_id",  # the field in the evaluation_scores collection
                "foreignField": "_id",  # the field in the benchmark collection
                "as": "benchmark_data",  # the name for the resulting array
            }
        },
        {
            "$unwind": "$benchmark_data"  # deconstructs the array from the previous stage
        },
        {"$match": {"benchmark_data.test_run_id": {"$in": test_run_ids}}},
        {
            "$project": {
                "_id": 0,  # exclude the _id field
                "percentage_score": 1,  # include the overall_score field
                "model": "$benchmark_data.model_params.model",
                "temperature": "$benchmark_data.model_params.temperature",
                "test_run_id": "$benchmark_data.test_run_id",
            }
        },
    ]

    results = DB.evaluation_scores.aggregate(pipeline)
    # print(list(results))
    return list(results)


# scores = get_scores_for_task_definition(
#     "{'name': 'Tavern', 'inhabitants: ['Bartender', 'Mercenary'], 'exits: [{'type': 'Door'}, {'type': 'Stairs'}]}"
# )


def generate_scatter_plot(scores):
    # Convert data to DataFrame
    df = pd.DataFrame(scores)
    print(df.columns)  # prints the column names
    print(df.empty)  # prints True if the DataFrame is empty, False otherwise

    # Scatter plot
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=df,
        x="temperature",
        y="percentage_score",
        hue="model",
        style="model",
        s=100,
    )
    plt.title("Percentage Score vs. Temperature")
    plt.xlabel("Temperature")
    plt.ylabel("Percentage Score")
    plt.legend(title="Model")
    plt.show()


def generate_box_plot(scores):
    print("Scores: ", scores)
    # Convert data to DataFrame
    df = pd.DataFrame(scores)
    print(df.columns)  # prints the column names
    print(df.empty)  # prints True if the DataFrame is empty, False otherwise

    # Box plot
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x="temperature", y="percentage_score", hue="model")
    plt.title("Distribution of Percentage Scores Across Temperatures")
    plt.xlabel("Temperature")
    plt.ylabel("Percentage Score")
    plt.legend(title="Model")
    plt.show()

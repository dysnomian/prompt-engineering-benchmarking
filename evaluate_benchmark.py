import json
import datetime
import re
import yaspin

from typing import List
from bson import ObjectId

from config import client, CONFIG
from db import DB

EVALUATOR_MODEL_PARAMS = CONFIG.get("evaluator", {"model": "gpt-3.5-turbo"})
LIVE_CALLS = True

STUBBED_RESPONSE = '{\n  "vivid": {\n    "score": 5,\n    "max_score": 5,\n    "comments": "The description paints a vivid picture of the cave chamber, with details like \'rocky and uneven\' floor, \'stalactites hang ominously,\' and \'cool and musty\' air. These elements help the reader visualize the setting effectively."\n  },\n  "clear": {\n    "score": 5,\n    "max_score": 5,\n    "comments": "The description is very clear and easy to understand. There is no ambiguity in the depiction of the cave chamber."\n  },\n  "tone": {\n    "score": 5,\n    "max_score": 5,\n    "comments": "The tone is appropriate for the context, conveying a sense of eeriness and isolation that fits well with the setting of a dimly lit cave chamber."\n  },\n  "includes_all_exits": {\n    "score": 5,\n    "max_score": 5,\n    "comments": "The description includes the only exit mentioned in the system prompt, which is a sturdy door."\n  },\n  "doesnt_make_up_exits": {\n    "score": 5,\n    "max_score": 5,\n    "comments": "The description does not mention any additional exits that were not included in the system prompt."\n  },\n  "doesnt_include_hidden_elements": {\n    "score": 0,\n    "max_score": 0,\n    "comments": "No hidden elements were mentioned in the system prompt, so this criterion is not applicable."\n  },\n  "includes_all_inhabitants": {\n    "score": 0,\n    "max_score": 0,\n    "comments": "There are no inhabitants mentioned in the system prompt, so this criterion is not applicable."\n  },\n  "doesnt_make_up_inhabitants": {\n    "score": 5,\n    "max_score": 5,\n    "comments": "The description does not invent any inhabitants that were not mentioned in the system prompt."\n  },\n  "doesnt_include_room_name": {\n    "score": 5,\n    "max_score": 5,\n    "comments": "The description does not explicitly state the room name, adhering to the criteria."\n  },\n  "implicit_time": {\n    "score": 0,\n    "max_score": 0,\n    "comments": "The system prompt does not include a time of day, so this criterion is not applicable."\n  },\n  "concise": {\n    "score": 5,\n    "max_score": 5,\n    "comments": "The description is concise and to the point, staying within the limit of 5 sentences and 250 characters."\n  }\n}'

evaluation_criteria = [
    {
        "name": "Vividness",
        "id": "vivid",
        "weight": 1,
        "description": "How vivid is the description? Does it paint a clear picture in the reader's mind?",
    },
    {
        "name": "Clarity",
        "id": "clear",
        "weight": 1,
        "description": "How clear is the description? Is it easy to understand? Is it ambiguous?",
    },
    {
        "name": "Tone",
        "id": "tone",
        "weight": 1,
        "description": "Is the tone of the description appropriate for the given context?",
    },
    {
        "name": "Includes all exits",
        "id": "includes_all_exits",
        "weight": 1,
        "description": "Does the description include all the exits that were mentioned in the system prompt?",
    },
    {
        "name": "Doesn't make up exits",
        "id": "doesnt_make_up_exits",
        "weight": 1,
        "description": "Does the description avoid mentioning new exits that were not mentioned in the system prompt?",
    },
    {
        "name": "Doesn't include hidden elements",
        "id": "doesnt_include_hidden_elements",
        "weight": 1,
        "description": "Does the description avoid describing any elements that were marked as hidden in the system prompt? If there are no hidden elements, this criterion is not applicable.",
    },
    {
        "name": "Includes all inhabitants",
        "id": "includes_all_inhabitants",
        "weight": 1,
        "description": "Does the description include all the inhabitants that were mentioned in the system prompt? If there are no inhabitants, this criterion is not applicable.",
    },
    {
        "name": "Doesn't make up inhabitants",
        "id": "doesnt_make_up_inhabitants",
        "weight": 1,
        "description": "Does the description avoid making up any inhabitants that were not mentioned in the system prompt?",
    },
    {
        "name": "Doesn't include room name",
        "id": "doesnt_include_room_name",
        "weight": 1,
        "description": "Does the description explicitly state the room name?",
    },
    {
        "name": "Implicitly includes time of day",
        "id": "implicit_time",
        "weight": 1,
        "description": "If included in the system prompt, does the description match up with what is expected given the time of day? If it mentions the time of day, does it do it in a natural way?",
    },
    {
        "name": "Conciseness",
        "id": "concise",
        "weight": 1,
        "description": "Is the description concise and to the point? Does it stay within the limit of 5 sentences or 250 characters?",
    },
]

example_output_json = json.dumps(
    {
        "vivid": {
            "score": 5,
            "max_score": 5,
            "comments": "The description paints a vivid picture of the cave chamber, with details like 'rocky and uneven' floor, 'stalactites hang ominously,' and 'cool and musty' air. These elements help the reader visualize the setting effectively.",
        },
        "includes_all_inhabitants": {
            "score": 0,
            "max_score": 0,
            "comments": "The description includes no inhabitants, but the task definition did not require them, so this criteria is not applicable.",
        },
    }
)


def evaluation_criteria_to_text(criteria) -> str:
    criteria_text = ""

    for idx, criterion in enumerate(criteria):
        criteria_text += f"{idx + 1}. {criterion['name']}: {criterion['description']} (JSON key: {criterion["id"]})\n"

    return criteria_text


evaluation_system_prompt = f"""You are a benchmark evaluation agent. You will be given the output of another agent in the form of a string, which will include its settings, system prompt, task prompt, and its description output. Your job is to evaluate the description and rank it based on the following criteria:

{evaluation_criteria_to_text(evaluation_criteria)}

Rank each criterion on a scale of 1-5, with 1 being the worst and 5 being the best. If a criterion is not applicable, comment on why, and set the score and max score for that criterion to 0. Please provide feedback on each criteria, explaining your ranking. Respond with a JSON object with a key for each criterion, and a value that is an object with the following keys:

- "comments": (string) Notes on how well the description meets this criteria.
- "score": (int) The score given for this criteria on a scale of 0-5.
- "max_score": (int) The maximum score possible for this criteria. Generally 5, can be 0 if no score was given.

The keys for each criterion 

Example output JSON (truncated for brevity):
{example_output_json}
"""


def save_evaluation_set(test_run_id, criteria, evaluation_model_params, system_prompt):
    evaluation_set_dict = {
        "test_run_id": test_run_id,
        "criteria": criteria,
        "evaluation_model_params": evaluation_model_params,
        "system_prompt": system_prompt,
        "created_at": datetime.datetime.now().isoformat(),
    }

    record = DB.evaluation_sets.insert_one(evaluation_set_dict)
    return record.inserted_id


def save_evaluation_scores(
    evaluation_set_id, scores, overall_score, overall_evaluation
):
    evaluation_dict = {
        "evaluation_set_id": evaluation_set_id,
        "scores": scores,
        "overall_score": overall_score,
        "overall_evaluation": overall_evaluation,
    }

    record = DB.evaluations.insert_one(evaluation_dict)
    return record.inserted_id


def generate_evaluation(benchmark):
    # response = STUBBED_RESPONSE
    response = client(
        {"model": EVALUATOR_MODEL_PARAMS["model"]}, evaluation_system_prompt, benchmark
    )

    print("Evaluation response: \n", response)
    return response


# def evaluate_benchmark_file(filename):
#     with open(filename, "r") as file:
#         output = file.read()

#     evaluation = evaluate_output(output)

#     # Append evaluation to the file
#     with open(filename, "a") as file:
#         file.write(f"\n\nEvaluation:\n{evaluation.choices[0].message.content}")

default_selection_params = {
    "unevaluated_only": True,
    "model": None,
    "task_run_ids": [],
}


def select_benchmarks(params: dict = {}):
    pipeline = []

    if params.get("unevaluated_only", default_selection_params["unevaluated_only"]):
        pipeline.append(
            {
                "$lookup": {
                    "from": "evaluation_scores",
                    "localField": "_id",
                    "foreignField": "benchmark_id",
                    "as": "scores",
                }
            }
        )
        pipeline.append({"$match": {"scores.benchmark_id": {"$exists": False}}})

    benchmarks = DB.benchmarks.find({"test_run_id": {"$in": test_run_ids}})
    return benchmarks


def evaluate_benchmark(
    benchmark_id,
    evaluation_set_id,
    eval_criteria=evaluation_criteria,
    unevaluated_only=True,
):
    if unevaluated_only:
        benchmark = DB.benchmarks.find_one({"_id": ObjectId(benchmark_id)})
    benchmark = DB.benchmarks.find_one({"_id": ObjectId(benchmark_id)})
    evaluation_response = generate_evaluation(benchmark["results"])
    evaluation_scores = json.loads(evaluation_response)

    # Calculate overall score
    overall_score = 0
    weighted_max_score = 0
    for score_name, score_dict in evaluation_scores.items():
        # get and store the weight on the record
        for item in eval_criteria:
            if item["id"] == score_name:
                print("item: ", item)
                print("score: ", score_dict)
                evaluation_scores[score_name]["weight"] = item["weight"]

        # calculate the weighted score, store it on the record
        score = score_dict["score"]
        max_score = score_dict["max_score"]
        weighted_score = score * evaluation_scores[score_name]["weight"]

        # add the weighted score to the overall score
        overall_score += weighted_score

        # add the weighted max score to the max score
        weighted_max_score += max_score * evaluation_scores[score_name]["weight"]

    # Save evaluation to database
    evaluation_score_dict = {
        "evaluation_set_id": evaluation_set_id,
        "benchmark_id": benchmark_id,
        "test_run_id": benchmark["test_run_id"],
        "evaluator_model": EVALUATOR_MODEL_PARAMS["model"],
        "scores": evaluation_scores,
        "overall_score": overall_score,
        "max_score": weighted_max_score,
        "percentage_score": overall_score / weighted_max_score * 100,
        "created_at": datetime.datetime.now().isoformat(),
    }

    record = DB.evaluation_scores.insert_one(evaluation_score_dict)
    return record.inserted_id


# def evaluate_benchmark_directory(directory):
#     for filename in os.listdir(directory):
#         if filename.endswith(".txt"):
#             evaluate_benchmark_file(os.path.join(directory, filename))


# def create_batch_benchmark_file(directory):
#     # create a csv file with the following columns: model, temperature, system prompt, task definition, results, overall score
#     with open("batch_evaluation.csv", "w") as file:
#         file.write(
#             "Model, Temperature, System Prompt, Task Definition, Results, Evaluation, Overall Score\n"
#         )

#     # iterate through all files in the directory
#     for filename in os.listdir(directory):
#         if filename.endswith(".txt"):
#             with open(os.path.join(directory, filename), "r") as file:
#                 print("Processing file: ", f"{directory}/{filename}")
#                 lines = file.readlines()
#                 print("lines: ", lines)
#                 model = lines[1].split(": ")[1].strip()
#                 temperature = lines[2].split(": ")[1].strip()
#                 sys_prompt = lines[3].split(": ")[1].strip()
#                 task_def = lines[4].split(": ")[1].strip()
#                 # results are the rest of the file
#                 results = "".join(lines[5:])
#                 print("filename: ", filename)
#                 print("results: ", results)

#                 evaluation = evaluate_output(results)

#                 print(evaluation.choices[0].message.content)

#                 return

#                 overall_score = (
#                     evaluation.choices[0]
#                     .message.content.split("Overall Score: ")[1]
#                     .split(" ")[0]
#                 )

#                 with open("batch_evaluation.csv", "a") as file:
#                     file.write(
#                         f"{model}, {temperature}, {sys_prompt}, {task_def}, {results}, {evaluation.choices[0].message.content}, {overall_score}\n"
#                     )


# create_batch_benchmark_file("benchmark_output")


def evaluate_test_run(test_run_id, unevaluated_only=True):
    with yaspin.yaspin(text="Evaluating benchmarks...", color="cyan") as spinner:
        spinner.write(f"Starting evaluation for test run {test_run_id}")
        benchmarks = list(DB.benchmarks.find({"test_run_id": test_run_id}))

        spinner.write(f"Found {len(benchmarks)} benchmarks.")

        evaluation_set_id = save_evaluation_set(
            test_run_id,
            evaluation_criteria,
            EVALUATOR_MODEL_PARAMS,
            evaluation_system_prompt,
        )

        spinner.write(f"Saved evaluation set {evaluation_set_id}")

        benchmark_counter = 0
        for benchmark in benchmarks:
            benchmark_counter += 1
            spinner.write(
                f"Evaluating benchmark {benchmark['_id']} ({benchmark_counter}/{len(benchmarks)})"
            )
            evaluate_benchmark(str(benchmark["_id"]), evaluation_set_id)


def evaluate_test_runs(test_run_ids: List[str]):
    for test_run_id in test_run_ids:
        evaluate_test_run(test_run_id)


def evaluate_task_definition(
    task_definition, criteria, evaluation_model_params, system_prompt
):
    benchmarks = DB.benchmarks.find({"task_definition": task_definition})
    evaluation_set_dict = {
        "task_definition": task_definition,
        "criteria": criteria,
        "evaluation_model_params": evaluation_model_params,
        "system_prompt": system_prompt,
        "created_at": datetime.datetime.now().isoformat(),
    }

    record = DB.evaluation_sets.insert_one(evaluation_set_dict)
    evaluation_set_id = record.inserted_id

    for benchmark in benchmarks:
        evaluate_benchmark(str(benchmark["_id"]), evaluation_set_id)


def evaluate_all_unevaluated_benchmarks():
    pipeline = [
        {
            "$lookup": {
                "from": "evaluation_scores",
                "localField": "_id",
                "foreignField": "benchmark_id",
                "as": "scores",
            }
        },
        {"$match": {"scores.benchmark_id": {"$ne": "$_id"}}},
        {"$project": {"_id": 1}},
    ]

    unevaluated_benchmarks = list(DB.benchmarks.aggregate(pipeline))

    # start evaluation_set
    evaluation_set_dict = {
        "query": str(pipeline),
        "criteria": evaluation_criteria,
        "evaluation_model_params": EVALUATOR_MODEL_PARAMS,
        "system_prompt": evaluation_system_prompt,
        "created_at": datetime.datetime.now().isoformat(),
    }

    record = DB.evaluation_sets.insert_one(evaluation_set_dict)
    evaluation_set_id = record.inserted_id

    for benchmark in unevaluated_benchmarks:
        evaluate_benchmark(str(benchmark["_id"]), evaluation_set_id)


def evaluate_new_benchmarks_for_model(model_name):
    pipeline = [
        {
            "$lookup": {
                "from": "evaluation_scores",
                "localField": "_id",
                "foreignField": "benchmark_id",
                "as": "evaluation_scores",
            }
        },
        {
            "$match": {
                "evaluation_scores": {"$size": 0},
                "model_params.model": {"$regex": re.compile(f"(?i)^{model_name}")},
            }
        },
        {"$project": {"_id": 1}},
    ]

    benchmarks = list(DB.benchmarks.aggregate(pipeline))
    print(f"Found {len(benchmarks)} new benchmarks for model {model_name}.")

    # start evaluation_set
    evaluation_set_dict = {
        "query": str(pipeline),
        "criteria": evaluation_criteria,
        "evaluation_model_params": EVALUATOR_MODEL_PARAMS,
        "system_prompt": evaluation_system_prompt,
        "created_at": datetime.datetime.now().isoformat(),
    }

    record = DB.evaluation_sets.insert_one(evaluation_set_dict)
    evaluation_set_id = record.inserted_id

    for benchmark in benchmarks:
        evaluate_benchmark(str(benchmark["_id"]), evaluation_set_id)

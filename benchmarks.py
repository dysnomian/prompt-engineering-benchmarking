import datetime
from yaspin import yaspin

from typing import Dict, Any, Union

from config import client, DEFAULT_MODEL_PARAMS, CONFIG
from db import DB


def prompt(
    model_config: Dict[str, Any],
    system_prompt: str,
    task_definition: str,
) -> Union[str, Dict[str, Any]]:
    # response = client(model_config).chat.completions.create(
    #     model=model_config.get("model", DEFAULT_MODEL_PARAMS["model"]),
    #     messages=[
    #         {"role": "system", "content": str(system_prompt)},
    #         {"role": "user", "content": str(task_definition)},
    #     ],
    #     temperature=model_config.get(
    #         "temperature", DEFAULT_MODEL_PARAMS["temperature"]
    #     ),
    #     max_tokens=model_config.get(
    #         "max_tokens", DEFAULT_MODEL_PARAMS["max_tokens"]
    #     ),
    #     top_p=model_config.get("top_p", DEFAULT_MODEL_PARAMS["top_p"]),
    #     frequency_penalty=model_config.get(
    #         "frequency_penalty", DEFAULT_MODEL_PARAMS["frequency_penalty"]
    #     ),
    #     presence_penalty=model_config.get(
    #         "presence_penalty", DEFAULT_MODEL_PARAMS["presence_penalty"]
    #     ),
    # )
    return client(model_config, system_prompt, task_definition)


model_configs = CONFIG["test_params"]["model_params"]
system_prompts = CONFIG["test_params"]["system_prompts"]
task_definitions = CONFIG["test_params"]["tasks"]


def save_test_run_info():
    full_configs = []

    for config in model_configs:
        full_configs.append({**DEFAULT_MODEL_PARAMS, **config})

    test_run_dict = {
        "started_at": datetime.datetime.now().isoformat(),
        "model_configs": full_configs,
        "system_prompts": system_prompts,
        "task_definitions": task_definitions,
    }

    record = DB.test_runs.insert_one(test_run_dict)
    return record.inserted_id


def save_benchmark(
    model_params: Dict[str, Any],
    system_prompt: str,
    task_definition: str,
    results: str,
    test_run_id: str,
):
    full_model_params = {**DEFAULT_MODEL_PARAMS, **model_params}

    benchmark_dict = {
        "model_params": full_model_params,
        "system_prompt": system_prompt,
        "task_definition": task_definition,
        "results": results,
        "test_run_id": test_run_id,
        "created_at": datetime.datetime.now().isoformat(),
    }
    record = DB.benchmarks.insert_one(benchmark_dict)
    return record.inserted_id


def run_benchmark():
    with yaspin(text="Running benchmarks...", color="cyan") as spinner:
        test_run_db_id = save_test_run_info()

        spinner.write(f"> Starting test run {test_run_db_id}.")

        results = ""
        for config in model_configs:
            full_config = {**DEFAULT_MODEL_PARAMS, **config}
            spinner.write(
                f"\n*** Starting {full_config['model']} (temperture: {full_config['temperature']})."
            )

            for system_prompt_id, system_prompt in system_prompts.items():
                spinner.write(f'> Benchmarking "{system_prompt_id}" system prompt.')
                for task_id, task_definition in task_definitions.items():
                    spinner.write(f'> Benchmarking "{task_id}" task.')
                    try:
                        results = prompt(full_config, system_prompt, task_definition)
                    except Exception as e:
                        print(e)
                    # save_to_file(
                    #     full_config,
                    #     system_prompt_id,
                    #     system_prompt,
                    #     task_id,
                    #     task_definition,
                    #     results,
                    # )
                    # append_to_test_run_csv(
                    #     full_config, system_prompt, task_definition, results
                    # )
                    save_benchmark(
                        full_config,
                        system_prompt,
                        task_definition,
                        str(results),
                        test_run_db_id,
                    )

    return results

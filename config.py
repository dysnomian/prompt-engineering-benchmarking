import os
import yaml

from typing import Union, Literal, Any, Dict

from openai import OpenAI
from anthropic import Anthropic

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

CONFIG_FILENAME = "config.yml"

FALLBACK_DEFAULT_PARAMS = {
    "model": "gpt-3.5-turbo",
    "temperature": 1.0,
    "max_tokens": 1024,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}


def load_config_file(filename=CONFIG_FILENAME) -> Dict[str, Any]:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Config file {CONFIG_FILENAME} not found.")
        return {"default_model_params": FALLBACK_DEFAULT_PARAMS}
    except yaml.YAMLError as e:
        print(f"Error loading config file: {e}")
        return {"default_model_params": FALLBACK_DEFAULT_PARAMS}


CONFIG = load_config_file()


DEFAULT_MODEL_PARAMS = CONFIG.get("default_model_params", FALLBACK_DEFAULT_PARAMS)

OPENAI_MODEL_NAMES = ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4", "gpt-4o", "gpt-3.5"]
ANTHROPIC_MODEL_NAMES = [
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku",
    "claude-2.1",
    "claude-2.0",
    "claude-instant-1.2",
]


def is_anthropic_model(model_params) -> Union[Literal[True], Literal[False]]:
    for model_name in ANTHROPIC_MODEL_NAMES:
        if model_params["model"].startswith(model_name):
            return True
    return False


def is_openai_model(model_params) -> Union[Literal[True], Literal[False]]:
    for openai_model_name in OPENAI_MODEL_NAMES:
        if model_params["model"].startswith(openai_model_name):
            return True
    return False


def is_lm_studio_model(model_params) -> Union[Literal[True], Literal[False]]:
    if "base_url" not in model_params and "api_key" not in model_params:
        return False
    return (
        model_params["base_url"].startswith("http://localhost")
        and model_params["api_key"] == "lm-studio"
    )


OUTPUT_DIR = "./benchmark_output"


def client_selector(model_params) -> Union[OpenAI, Anthropic]:
    if is_openai_model(model_params):
        return OpenAI(api_key=OPENAI_API_KEY)
    elif is_lm_studio_model(model_params):
        return OpenAI(
            base_url=model_params["base_url"], api_key=model_params["api_key"]
        )
    elif is_anthropic_model(model_params):
        return Anthropic(api_key=ANTHROPIC_API_KEY)
    else:
        return OpenAI(
            base_url=model_params["base_url"], api_key=model_params["api_key"]
        )


def client(
    model_params, system_prompt: str, task_definition: str
) -> Union[str, Dict[str, Any]]:
    llm_client = client_selector(model_params)

    if type(llm_client) == OpenAI:
        completions_api_call = llm_client.chat.completions.create(
            model=model_params.get("model", DEFAULT_MODEL_PARAMS["model"]),
            messages=[
                {"role": "system", "content": str(system_prompt)},
                {"role": "user", "content": str(task_definition)},
            ],
            temperature=model_params.get(
                "temperature", DEFAULT_MODEL_PARAMS["temperature"]
            ),
            max_tokens=model_params.get(
                "max_tokens", DEFAULT_MODEL_PARAMS["max_tokens"]
            ),
            top_p=model_params.get("top_p", DEFAULT_MODEL_PARAMS["top_p"]),
            frequency_penalty=model_params.get(
                "frequency_penalty", DEFAULT_MODEL_PARAMS["frequency_penalty"]
            ),
            presence_penalty=model_params.get(
                "presence_penalty", DEFAULT_MODEL_PARAMS["presence_penalty"]
            ),
        )

        if completions_api_call.choices[0].message.content:
            return completions_api_call.choices[0].message.content
        return {"error": "Error: No response from API."}
    elif type(llm_client) == Anthropic:
        messages_api_response = llm_client.messages.create(
            max_tokens=1024,
            messages=[
                {"role": "user", "content": task_definition},
            ],
            model=model_params.get("model", DEFAULT_MODEL_PARAMS["model"]),
            system=system_prompt,
            temperature=model_params.get(
                "temperature", DEFAULT_MODEL_PARAMS["temperature"]
            ),
        )

        return messages_api_response.content[0].text
    else:
        return f"Error: No client found for model {model_params['model']}"


def list_test_runs():
    subdirectories = [
        name
        for name in os.listdir(OUTPUT_DIR)
        if os.path.isdir(os.path.join(OUTPUT_DIR, name))
    ]
    return subdirectories


def new_test_run_id():
    subdirectories = list_test_runs()

    if subdirectories:
        highest_number = max([int(name) for name in subdirectories])
        return highest_number + 1
    else:
        return 1

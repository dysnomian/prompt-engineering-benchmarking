from openai import OpenAI
import os
from google.colab import userdata

OPENAI_API_KEY = userdata.get('OPENAI_API_KEY')
print(OPENAI_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://rather-square-fatal-titled.trycloudflare.com/v1")

def prompt(language_model, system_prompt, task_definition):

  response = client.chat.completions.create(
    model=language_model,
    messages=[
      {
        "role": "system",
        "content": system_prompt
      },
      {
        "role": "user",
        "content": task_definition
      }
    ],
    temperature=1.5,
    max_tokens=1000,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
  )
  return response.choices[0].message.content

import datetime

def save_to_file(language_model, system_prompt, task_definition, results):
  filename = datetime.datetime.now()
  filename = filename.strftime("%Y%m%d%H%M%S%f")
  file_contents = f"""
  Language Model: {language_model}
  System Prompt: {system_prompt}
  Task Definition: {task_definition}
  Results: {results}
  """
  file = open("./" + filename + '.txt', 'w')
  file.write(file_contents)
  file.close()
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class CodeGeneratorAgent:
    def __init__(self):
        print(f"CodeGeneratorAgent initialized")

    def run(self, task_data):
        prompt = f"Task: {task_data['description']}\n..."
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY",""),
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Act as a Python AI expert engineer.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=10000
        )
        print(response.choices[0].message.content)

        code_snippet = response.choices[0].message.content
        print(f"code_snippet result {code_snippet}")
        return code_snippet

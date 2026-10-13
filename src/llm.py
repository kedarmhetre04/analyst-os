import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "gpt-5.6-luna"

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=120,
    max_retries=3,
)


class LLMOutputError(ValueError):
    def __init__(self, message, raw_output):
        super().__init__(message)
        self.raw_output = raw_output


def generate_text(instructions, prompt):
    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=prompt,
    )

    return response.output_text


def generate_json(instructions, prompt, schema_name, schema):
    """
    Call the model with a strict JSON schema (Structured Outputs)
    and return the parsed object.
    """
    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": schema,
                "strict": True,
            }
        },
    )

    raw_output = response.output_text

    try:
        return json.loads(raw_output)

    # Strict schemas make this rare, but refusals or truncated
    # responses can still produce non-JSON output.
    except json.JSONDecodeError as error:
        raise LLMOutputError(
            f"{schema_name} returned invalid JSON",
            raw_output,
        ) from error

import json
import os

from google import genai


class GeminiRecoveryClient:
    """
    Gemini API adapter for RecoverAI.

    The model returns a strict AgentDecision JSON object.
    The API key is read from GEMINI_API_KEY.
    """

    def __init__(self, model: str | None = None):
        import sys

        print("PYTHON:", sys.executable)

        import google

        print("GOOGLE MODULE:", google)
        print("GOOGLE PATH:", getattr(google, "__path__", None))

        from google import genai

        print("GENAI MODULE:", genai)

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when USE_LLM=true")

        self.client = genai.Client(api_key=api_key)
        self.model = model or os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash",
        )

    def generate_structured(
        self,
        system: str,
        input: dict,
        schema,
    ) -> dict:

        response = self.client.models.generate_content(
            model=self.model,
            contents=(
                f"{system}\n\n"
                "Payment recovery case:\n"
                f"{json.dumps(input, indent=2)}"
            ),
            config={
                "response_mime_type": "application/json",
                "response_schema": schema.model_json_schema(),
            },
        )

        return json.loads(response.text)
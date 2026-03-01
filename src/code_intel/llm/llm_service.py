from openai import OpenAI
import os

class LLMService:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL"),
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

    def summarize_function(self, source_code: str) -> str:
        prompt = f"""
        You are a senior software engineer.
        Summarize what this Python function does in 1-2 clear sentences.

        Function code:
        {source_code}
        """

        response = self.client.chat.completions.create(
            model="anthropic/claude-opus-4.6",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        return response.choices[0].message.content.strip()

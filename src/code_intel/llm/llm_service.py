from openai import OpenAI
import os

class LLMService:
    def __init__(self):
        base_url = os.getenv("OPENROUTER_BASE_URL") or os.getenv("KIRO_BASE_URL")
        self.client = OpenAI(
            base_url=base_url,
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

    def explain_impact(self, function_name: str, impact_data: list, risk_score: int) -> str:
        formatted_impact = "\n".join(
            f"- {item['name']} (depth: {item['depth']})"
            for item in impact_data
        )

        prompt = f"""
        You are a senior software architect analyzing a Python codebase.

        Function changed: {function_name}

        Downstream impact:
        {formatted_impact}

        Risk score: {risk_score}

        Explain in 4-6 concise technical sentences:
        - How change propagates
        - Why this risk score makes sense
        - What developers should be cautious about
        Keep it practical and engineering-focused.
        """

        response = self.client.chat.completions.create(
            model="anthropic/claude-opus-4.6",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        return response.choices[0].message.content.strip()
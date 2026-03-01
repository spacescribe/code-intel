import re 

class SimpleAgent:
    def __init__(self, llm_service, tool_registry):
        self.llm = llm_service
        self.tools = tool_registry

    def run(self, user_input: str):
        system_prompt = """
You are a code intelligence agent.

You have access to these tools:

1. get_impact(function_name)
   - Returns downstream impact and risk score.

2. get_dead_code()
   - Returns unused functions.

3. search_memory(query)
   - Searches semantic memory of function summaries.

If you need a tool, respond EXACTLY in this format:
CALL tool_name {"param": "value"}

If no tool is needed, answer normally.
"""

        response = self.llm.client.chat.completions.create(
            model="anthropic/claude-opus-4.6",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0
        )

        message = response.choices[0].message.content.strip()

        print("\n🧠 Agent reasoning:")
        print(message)

        # Manual tool parsing
        tool_match = re.search(r'CALL \w+ \{.*\}', message)

        if tool_match:
            tool_call = tool_match.group(0)
            return self._handle_tool_call(tool_call, user_input)

        return message

    def _handle_tool_call(self, message: str, original_question: str):
        import json
        import re

        match = re.match(r'CALL (\w+) (.*)', message)
        if not match:
            return "Invalid tool call format."

        tool_name = match.group(1)
        params = json.loads(match.group(2))

        # Execute tool
        tool_function = getattr(self.tools, tool_name, None)
        if not tool_function:
            return f"Unknown tool: {tool_name}"

        tool_result = tool_function(**params)

        # Send tool result back to LLM for final answer
        followup_prompt = f"""
User question: {original_question}

Tool result:
{tool_result}

Provide a final, helpful answer to the user.
"""

        final_response = self.llm.client.chat.completions.create(
            model="anthropic/claude-opus-4.6",
            messages=[{"role": "user", "content": followup_prompt}],
            temperature=0
        )

        return final_response.choices[0].message.content.strip()
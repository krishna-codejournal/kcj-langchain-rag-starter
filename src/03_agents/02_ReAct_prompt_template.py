
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

### 1. The ReAct Prompt Template
""" 
The secret sauce is the System Prompt. It tells the model exactly how to format its thoughts and how to use the tools provided.
"""

SYSTEM_PROMPT = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer.

Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

1. calculate:
e.g. calculate: 4 * 7 / 3
Runs a mathematical calculation.

2. wikipedia:
e.g. wikipedia: Hubble Space Telescope
Returns a summary from Wikipedia.

Example session:

Question: What is the capital of France and its current population?
Thought: I need to look up the capital of France and then find its population.
Action: wikipedia: France
PAUSE

You will be called again with this:
Observation: France is a country in Europe. Its capital is Paris.

Thought: I now know the capital is Paris. Now I need the population of Paris.
Action: wikipedia: Paris
PAUSE

... and so on until you reach an Answer.
""".strip()

## 2. The Implementation Loop
""" Here is a simplified logic flow. In a real scenario, you would replace the query_llm and execute_action placeholders with actual API calls. """

def react_agent(user_question):
    history = f"Question: {user_question}"
    
    # Limit loops to prevent infinite runs
    for i in range(5):
        # 1. Get response from LLM (passing system prompt + history)
        response = query_llm(SYSTEM_PROMPT, history)
        print(f"\n--- Iteration {i+1} ---\n{response}")
        
        if "Answer:" in response:
            return response
        
        # 2. Extract Action from the response
        # Simple regex or string parsing to find "Action: tool_name: argument"
        action, arg = extract_action(response)
        
        # 3. Execute the tool
        observation = execute_action(action, arg)
        
        # 4. Update history with the result and loop back
        history += f"\nObservation: {observation}"

    return "Max iterations reached."

def query_llm(system_prompt, history, model="gpt-4o"):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": history}
    ]
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0  # Vital for structural consistency
    )
    
    return response.choices[0].message.content

import re

def extract_action(llm_output):
    # This regex looks for "Action: tool_name: argument"
    # It is case-sensitive by default to match your prompt instructions
    pattern = r"Action:\s*(\w+):\s*(.*)"
    match = re.search(pattern, llm_output)
    
    if match:
        action_name = match.group(1).strip()
        action_input = match.group(2).strip()
        return action_name, action_input
    
    return None, None


def execute_action(action_name, action_input):
    # Mapping tool names to actual Python functions
    tools = {
        "calculate": lambda x: str(eval(x)), # Note: use a safer math library in production!
        "wikipedia": search_wikipedia_function 
    }
    
    if action_name in tools:
        print(f"--- Running {action_name} for: {action_input} ---")
        return tools[action_name](action_input)
    else:
        return f"Error: Tool {action_name} not found."
    
import wikipedia

def search_wikipedia_function(q):
    """
    Searches Wikipedia for a query and returns the summary of the best match.
    """
    try:
        # We limit the summary to 2-3 sentences to keep the ReAct loop efficient
        return wikipedia.summary(q, sentences=3)
    
    except wikipedia.exceptions.DisambiguationError as e:
        # If the query is too vague, return the list of possible options
        return f"Ambiguous query. Did you mean: {', '.join(e.options[:5])}?"
    
    except wikipedia.exceptions.PageError:
        # If no page exists, inform the agent so it can try a different search term
        return "No Wikipedia page found for this query. Try a different search term."
    
    except Exception as e:
        return f"An error occurred: {str(e)}"
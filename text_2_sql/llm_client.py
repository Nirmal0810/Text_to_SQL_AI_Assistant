import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL_NAME = "models/gemini-2.5-pro"

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0):
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_prompt
    )

    response = model.generate_content(
        user_prompt,
        generation_config={
            "temperature": temperature
        }
    )

    return response.text.strip()

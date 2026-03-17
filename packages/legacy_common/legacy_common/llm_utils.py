import openai
import requests

OPENAI_API_KEY = "REDACTED_KEY"
openai.api_key = OPENAI_API_KEY
OPENAI_MODEL = "gpt-4.1-nano"
OPENAI_MAX_TOKENS = 1500

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "starcoder2"
OLLAMA_MAX_TOKENS = 1500

# --- Call OpenAI GPT-4o model ---
def call_ollama(prompt, model=OLLAMA_MODEL, max_tokens=OLLAMA_MAX_TOKENS):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": max_tokens
            }
        }
    )
    response.raise_for_status()
    return response.json()["response"].strip()

def call_openai(prompt, model=OPENAI_MODEL, max_tokens=OPENAI_MAX_TOKENS):
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for generating C++ Doxygen comments."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[!] OpenAI API error: {e}")
        return ""

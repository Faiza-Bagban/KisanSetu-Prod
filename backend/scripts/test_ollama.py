import ollama

response = ollama.chat(model="llama3.1:8b", messages=[
    {"role": "user", "content": "In one sentence, is a farmer with 2 acres of land eligible for a scheme requiring max 5 acres?"}
])

print(response["message"]["content"])
#!/bin/bash

# Check if enough arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <document_file> <prompt>"
  exit 1
fi

# First argument: File containing the document strings
DOCUMENTS_FILE="$1"

# Second argument: User input prompt
USER_PROMPT="$2"

# Python script output file
OUTPUT_PYTHON_SCRIPT="generated_script.py"

# Generate the Python script
cat <<EOF > "$OUTPUT_PYTHON_SCRIPT"
import ollama
import chromadb

documents = [
$(cat $DOCUMENTS_FILE)
]

client = chromadb.Client()
collection = client.create_collection(name="docs")

# Store each document in a vector embedding database
for i, d in enumerate(documents):
  response = ollama.embeddings(model="llama3", prompt=d)
  embedding = response["embedding"]
  collection.add(
    ids=[str(i)],
    embeddings=[embedding],
    documents=[d]
  )

# Use the command line argument for the prompt
prompt = "$USER_PROMPT"

# Generate an embedding for the prompt and retrieve the most relevant doc
response = ollama.embeddings(
  prompt=prompt,
  model="llama3"
)
results = collection.query(
  query_embeddings=[response["embedding"]],
  n_results=1
)
data = results['documents'][0][0]

# Generate a response combining the prompt and data we retrieved in step 2
output = ollama.generate(
  model="llama3",
  prompt=f"Using this data: {data}. Respond to this prompt: {prompt}"
)

print(output['response'])
EOF

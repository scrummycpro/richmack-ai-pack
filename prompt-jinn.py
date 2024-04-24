import sys
import ollama
import chromadb

# Check if both a file path and prompt question are provided as command line arguments
if len(sys.argv) > 2:
    file_path = sys.argv[1]
    prompt = sys.argv[2]
else:
    print("Usage: python script.py <path_to_text_file> <prompt_question>")
    sys.exit(1)

# Read the content of the file
with open(file_path, 'r') as file:
    documents = [line.strip() for line in file.readlines() if line.strip()]  # Read and strip each line, excluding empty lines

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

# Generate an embedding for the prompt and retrieve the most relevant document
response = ollama.embeddings(
    prompt=prompt,
    model="llama3"
)
results = collection.query(
    query_embeddings=[response["embedding"]],
    n_results=1
)

# Check if any documents were returned
if results['documents']:
    data = results['documents'][0][0]

    # Generate a response combining the prompt and data we retrieved
    output = ollama.generate(
        model="llama3",
        prompt=f"Using this data: {data}. Respond to this prompt: {prompt}"
    )

    # Print the generated response
    if 'response' in output and output['response']:
        print(output['response'])
    else:
        print("No response generated.")
else:
    print("No relevant documents found.")

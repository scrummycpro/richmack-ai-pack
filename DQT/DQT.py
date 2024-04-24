import tkinter as tk
from tkinter import filedialog, messagebox, Menu
import os
import sqlite3
import ollama
import chromadb

# Create SQLite database connection
conn = sqlite3.connect('responses.db')
c = conn.cursor()

# Create responses table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS responses
             (role TEXT, technology TEXT, response TEXT)''')
conn.commit()

def upload_document():
    file_path = filedialog.askopenfilename()
    if file_path:
        with open(file_path, 'r') as file:
            documents = file.readlines()
            # Clear previous content in the document_text_entry
            document_text_entry.delete(1.0, tk.END)
            # Insert the documents into the document_text_entry
            for document in documents:
                document_text_entry.insert(tk.END, document)

def generate_response():
    role = role_entry.get()
    technology = tech_entry.get()
    document_text = document_text_entry.get(1.0, tk.END).strip()
    
    # Initialize chromadb client
    client = chromadb.Client()
    
    try:
        # Attempt to query the collection to check if it exists
        collection = client.get_collection(name="docs")
    except ValueError as e:
        # Collection doesn't exist, so we create a new one
        if str(e) == f"Collection docs does not exist.":
            collection = client.create_collection(name="docs")
        else:
            # Other unexpected error
            raise e

    # Generate embedding for the document text
    response = ollama.embeddings(model="mistral", prompt=document_text)
    embedding = response["embedding"]
    collection.add(
        ids=['uploaded_document'],
        embeddings=[embedding],
        documents=[document_text]
    )

    # Construct the prompt with placeholders for parameters
    prompt_template = "In the form: is, is not, should be associated with, should not be associated with, what is {role} in regards to {technology}?"
    prompt = prompt_template.format(role=role, technology=technology)

    # Generate an embedding for the prompt and retrieve the most relevant document
    response = ollama.embeddings(
        prompt=prompt,
        model="mistral"
    )
    results = collection.query(
        query_embeddings=[response["embedding"]],
        n_results=1
    )
    data = results['documents'][0][0]

    # Generate a response combining the prompt and data we retrieved
    output = ollama.generate(
        model="mistral",
        prompt=f"Using this data: {data}. Respond to this prompt: {prompt}"
    )
    
    response_text.delete(1.0, tk.END)  # Clear previous response
    response_text.insert(tk.END, output['response'])
    
    # Save response to SQLite database
    c.execute("INSERT INTO responses (role, technology, response) VALUES (?, ?, ?)",
              (role, technology, output['response']))
    conn.commit()

def copy_text():
    root.clipboard_clear()
    text = root.focus_get()
    if text:
        selected_text = text.selection_get()
        root.clipboard_append(selected_text)

def paste_text():
    text = root.focus_get()
    if text:
        text.insert(tk.INSERT, root.clipboard_get())

def select_all(event=None):
    text = root.focus_get()
    if text:
        text.tag_add(tk.SEL, "1.0", tk.END)
        text.mark_set(tk.INSERT, "1.0")
        text.see(tk.INSERT)
        return 'break'

def save_response():
    response = response_text.get(1.0, tk.END).strip()
    if response:
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(response)
                messagebox.showinfo("Save", "Response saved successfully.")

# Create the main window
root = tk.Tk()
root.title("Document Query Tool")

# Create entry fields for role and technology
role_label = tk.Label(root, text="Enter Role:")
role_label.grid(row=0, column=0, padx=5, pady=5)
role_entry = tk.Entry(root)
role_entry.grid(row=0, column=1, padx=5, pady=5)

tech_label = tk.Label(root, text="Enter Technology:")
tech_label.grid(row=1, column=0, padx=5, pady=5)
tech_entry = tk.Entry(root)
tech_entry.grid(row=1, column=1, padx=5, pady=5)

# Create a button to upload a document
upload_button = tk.Button(root, text="Upload Document", command=upload_document)
upload_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

# Create a text widget to display the uploaded document
document_text_label = tk.Label(root, text="Uploaded Document Text:")
document_text_label.grid(row=3, column=0, padx=5, pady=5)
document_text_entry = tk.Text(root, height=5, width=50)
document_text_entry.grid(row=3, column=1, padx=5, pady=5)

# Create a button to generate response
generate_button = tk.Button(root, text="Generate Response", command=generate_response)
generate_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

# Create a text widget to display the response
response_text_label = tk.Label(root, text="Generated Response:")
response_text_label.grid(row=5, column=0, padx=5, pady=5)
response_text = tk.Text(root, height=10, width=70)
response_text.grid(row=5, column=1, padx=5, pady=5)
response_text.config(wrap='word')  # Wrap text based on word boundaries

# Create a right-click menu for response text
response_text_menu = Menu(root, tearoff=0)
response_text_menu.add_command(label="Copy", command=copy_text)
response_text_menu.add_command(label="Paste", command=paste_text)
response_text_menu.add_command(label="Select All", command=select_all)
response_text.bind("<Button-3>", lambda e: response_text_menu.post(e.x_root, e.y_root))

# Create a button to save response
save_button = tk.Button(root, text="Save Response", command=save_response)
save_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

# Run the main event loop
root.mainloop()

# Close SQLite connection
conn.close()

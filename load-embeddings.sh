#!/bin/bash

# Get the current date
current_date=$(date +"%Y-%m-%d")

# Define the input file name
input_file="${current_date}_load.txt"

# Define the SQLite database name using the current date
db_name="${current_date}_news_embeddings.db"

# Create the SQLite database with the specified name
sqlite3 "$db_name" <<EOF
CREATE TABLE IF NOT EXISTS news_embeddings (
    date TEXT,
    line TEXT
);
EOF

# Read each line from the input file and insert into the SQLite database
while IFS= read -r line; do
    # Print each line to verify
    echo "Line: $line"
    # Insert each line into the SQLite database
    sqlite3 "$db_name" "INSERT INTO news_embeddings (date,line) VALUES ('$current_date','$line');"
done < "$input_file"

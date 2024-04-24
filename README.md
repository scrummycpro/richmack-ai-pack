## Extracting and Tokenizing Articles from Newboat RSS Feed

This guide outlines the process of extracting and tokenizing articles from the Newboat RSS feed, adding them to a SQLite database named "news_embeddings," and shipping them to Amazon S3 for further processing into a PostgreSQL container. This approach can help save on Amazon RDS pricing by attaching a volume to the PostgreSQL container, allowing the database to be loaded into a larger database warehouse.

### Step 1: Extract and Tokenize Articles

To extract articles from the Newboat RSS feed and tokenize them into sentences, use the following commands:

```bash
# Query all information
sqlite3 cache.db -json "SELECT pubdate, title, author, url, content FROM rss_item" | jq '.[] | del(.content) + {content: (.content | gsub("<[^>]*>"; "") | gsub("\n"; "") | gsub("\\\\"; ""))}'

# Title, URLs, and content
sqlite3 cache.db -json "SELECT title, url, content FROM rss_item" | jq '.[] | del(.content) + {content: (.content | gsub("<[^>]*>"; "") | gsub("\n"; "") | gsub("\\\\"; ""))}'

# Content only
sqlite3 cache.db -json "SELECT content FROM rss_item" | jq '.[] | del(.content) + {content: (.content | gsub("<[^>]*>"; "") | gsub("\n"; "") | gsub("\\\\"; ""))}'

# Parsing for embedding; tokenizing each sentence
sqlite3 cache.db "SELECT title, content FROM rss_item" | sed -E 's/<[^>]*>//g; s/\\//g; s/\\n/ /g' | sed -E 's/([.!?])/\1\n/g' | sed 's/^/"/;s/$/"/' | sed '$!s/$/,/'|grep -v '""'

# Add the embeddings to a file
sqlite3 cache.db "SELECT title, content FROM rss_item" | sed -E 's/<[^>]*>//g; s/\\//g; s/\\n/ /g' | sed -E 's/([.!?])/\1\n/g' | sed 's/^/"/;s/$/"/' | sed '$!s/$/,/'|sed s'/|//g'|grep -v '""'|grep -v '" "'|tee -a $(date +"%Y-%m-%d")_news_embeddings

# Remove the quotes and commas for processing (just in case)
sed "$(date +"%Y-%m-%d")_news_embeddings" -e 's/^"//g' -e 's/",//g' > "$(date +"%Y-%m-%d")_load.txt"
```


# There was an error generating the embeddings when double quotes are in the tokenized sentence, run this sed command to solve:

sed -i ':a;s/\(.\)"\(.*"\)/\1\2/;ta' 2024-04-23_news_embeddings

### Step 2: Insert Tokenized Sentences into SQLite Database

Use the following script to insert the tokenized sentences into a SQLite3 database named `$current_date_news-embeddings.db`:

```bash
#!/bin/bash

# Get the current date
current_date=$(date +"%Y-%m-%d")

# Define the input file name
input_file="${current_date}_load.txt"

# Define the SQLite database name using the current date
db_name="${current_date}_news-embeddings.db"

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
```

Replace `$current_date` with the current date (e.g., `2022-04-26`). This script will create a SQLite database named `2022-04-26_news-embeddings.db` and insert each tokenized sentence along with the current date into the `news_embeddings` table.

### Step 3: Shipping to Amazon S3 for PostgreSQL Container Processing

After inserting the data into the SQLite database, you can ship the database file to Amazon S3 for further processing into a PostgreSQL container. This approach allows you to save on Amazon RDS pricing by attaching a volume to the PostgreSQL container and loading the database into a larger database warehouse.

### Conclusion

By following this approach, you can efficiently extract articles from the Newboat RSS feed, tokenize them into sentences, store them in a SQLite database, and ship them to Amazon S3 for processing into a PostgreSQL container. This method helps optimize costs by leveraging containerized databases and cloud storage solutions.
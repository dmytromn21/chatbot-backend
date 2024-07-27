import csv
import json

from openai import OpenAI

# Set up your OpenAI API key
client = OpenAI(api_key="sk-proj-Zhm6xQUqTCg3omqOws2QT3BlbkFJMzG65F1LwKDNzzZWyxFE")


def generate_embedding(text):
    response = client.embeddings.create(input=text, model="text-embedding-ada-002")
    return response.data[0].embedding


def process_csv(file_path, max_rows):
    events = []
    row_count = 0

    with open(file_path) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row_count >= max_rows:
                break

            event = {
                "Id": row_count + 1,
                "Name": row["title"],
                "Description": row["summary"],
                "Category": row["tags"],
                "Price": parsed_price(row["min_price"]),
                "Start Date": row["start_date"],
                "Embedding": [],
            }

            # Generate embedding
            embedding_text = f"{row['title']} {row['summary']} {row['tags']}"
            event["Embedding"] = generate_embedding(embedding_text)

            events.append(event)
            row_count += 1

    return events


def parsed_price(value, default=0.00):
    if value and isinstance(value, str):
        value = value.strip().lower()
        if value == "none" or value == "":
            return None
        try:
            return float(value)
        except ValueError:
            return None
    elif isinstance(value, (int, float)):
        return float(value)
    return None


# Process the CSV and generate JSON
csv_file_path = "miami_download.csv"
events_data = process_csv(csv_file_path, max_rows=2365)

# Save to JSON file
with open("events_with_embeddings.json", "w") as jsonfile:
    json.dump(events_data, jsonfile, indent=2)

print(f"Processed {len(events_data)} events and saved to events_with_embeddings.json")

import json
import csv

input_file = "../../data/input.jsonl"
output_file = "../../data/classify.csv"

with open(input_file, "r", encoding="utf-8") as infile, \
     open(output_file, "w", newline="", encoding="utf-8") as outfile:

    writer = csv.writer(outfile)
    writer.writerow(["event", "extra_info"])  # header

    for line in infile:
        data = json.loads(line)

        events = data.get("events", [])
        for event in events:
            event_text = event.get("event", "")
            extra_info = event.get("extra_info", "").strip()
            writer.writerow([event_text, extra_info])

print(f"Saved CSV to {output_file}")
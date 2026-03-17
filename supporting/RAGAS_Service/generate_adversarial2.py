import csv
from transformers import MarianMTModel, MarianTokenizer
from tqdm import tqdm

input_csv = "../../data/classify.csv"
output_csv = "output.csv"
labels_to_augment = ["STORY", "NSPECIFIC"]
intermediate_lang = "fr"
num_return_sequences = 1

# English to Intermediate language
model_name_src = f"Helsinki-NLP/opus-mt-en-{intermediate_lang}"
tokenizer_src = MarianTokenizer.from_pretrained(model_name_src)
model_src = MarianMTModel.from_pretrained(model_name_src)

# Intermediate language to English
model_name_back = f"Helsinki-NLP/opus-mt-{intermediate_lang}-en"
tokenizer_back = MarianTokenizer.from_pretrained(model_name_back)
model_back = MarianMTModel.from_pretrained(model_name_back)

def back_translate(text):
    # Step 1: English to Intermediate
    batch = tokenizer_src([text], return_tensors="pt", padding=True)
    translated = model_src.generate(**batch, max_length=256)
    intermediate_text = tokenizer_src.decode(translated[0], skip_special_tokens=True)

    # Step 2: Intermediate to English
    batch_back = tokenizer_back([intermediate_text], return_tensors="pt", padding=True)
    back_translated = model_back.generate(**batch_back, max_length=256, num_beams=5, num_return_sequences=num_return_sequences)
    augmented_texts = [tokenizer_back.decode(t, skip_special_tokens=True) for t in back_translated]
    return augmented_texts

augmented_rows = []

with open(input_csv, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in tqdm(reader, desc="Processing CSV"):
        event = row["event"]
        label = row["extra_info"]

        # Keep original row
        augmented_rows.append({"event": event, "label": label})

        # Only augment certain labels
        if label in labels_to_augment:
            try:
                new_texts = back_translate(event)
                for t in new_texts:
                    augmented_rows.append({"event": t, "label": label})
            except Exception as e:
                print(f"Error back-translating row: {event}")
                print(e)

with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["event", "label"])
    writer.writeheader()
    for row in augmented_rows:
        writer.writerow(row)

print(f"Saved augmented dataset to {output_csv}")
print(f"Original size: {len(augmented_rows)} rows (includes originals + augmented)")
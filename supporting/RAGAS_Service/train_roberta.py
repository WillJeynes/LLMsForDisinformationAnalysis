from transformers import RobertaTokenizer, RobertaForSequenceClassification, Trainer, TrainingArguments
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from collections import Counter
import sys
import csv

NUM_CLASSES = 2
model_name = "roberta-base"

LABEL_PRIORITY = [
    ("PERFECT", 0),
    ("STORY", 1),
    ("NSPECIFIC", 1),
    ("REWORDING", 1),
    ("TINCORRECT", -1),
    ("DUPLICATE", -1),
    ("", 0),  # fallback to PERFECT
]

def label_to_int(extra_info: str) -> int:
    """
    Convert extra_info string to integer label using priority rules.
    """

    if extra_info is None:
        extra_info = ""

    extra_info = extra_info.strip()

    # Handle empty string explicitly
    if extra_info == "":
        for key, value in LABEL_PRIORITY:
            if key == "":
                return value
        raise ValueError("Empty extra_info but no empty mapping defined")

    # Split words (case-insensitive)
    tokens = set(extra_info.upper().split())

    # Priority matching
    for key, value in LABEL_PRIORITY:
        if key == "":
            continue

        if key in tokens:
            return value

    raise ValueError(f"Unknown label content: '{extra_info}'")


def load_dataset_from_csv(path):
    texts = []
    labels = []

    removed_rows = 0

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader, start=1):
            text = row["event"]
            label_str = row["extra_info"]

            try:
                label_int = label_to_int(label_str)
            except Exception as e:
                print(f"ERROR converting label on line {i}: {label_str}")
                print(e)
                sys.exit(1)

            # Skip rows marked for removal
            if label_int == -1:
                removed_rows += 1
                continue

            texts.append(text)
            labels.append(label_int)

    print(f"Loaded {len(texts)} samples (removed {removed_rows})")

    return texts, labels



def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = logits.argmax(axis=1)

    return {
        "accuracy": accuracy_score(labels, preds),
        "f1": f1_score(labels, preds, average="weighted"),
        "precision": precision_score(labels, preds, average="weighted"),
        "recall": recall_score(labels, preds, average="weighted"),
    }

texts, labels = load_dataset_from_csv("../../data/classify.csv")

tokenizer = RobertaTokenizer.from_pretrained(model_name)
model = RobertaForSequenceClassification.from_pretrained(
    model_name,
    num_labels=NUM_CLASSES
)

for param in model.roberta.parameters():
    param.requires_grad = False

for param in model.roberta.encoder.layer[-2:].parameters():
    param.requires_grad = True

print("Dataset size:", len(texts))
print("Label distribution:")
print(Counter(labels))

train_texts, val_texts, train_labels, val_labels = train_test_split(
    texts,
    labels,
    test_size=0.2,
    random_state=42
)

train_encodings = tokenizer(
    train_texts,
    truncation=True,
    padding=True,
    max_length=256
)

val_encodings = tokenizer(
    val_texts,
    truncation=True,
    padding=True,
    max_length=256
)

class TextDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {
            key: torch.tensor(val[idx])
            for key, val in self.encodings.items()
        }
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

training_args = TrainingArguments(
    output_dir="./results",
    learning_rate=1e-5,
    per_device_train_batch_size=8,
    num_train_epochs=15,
    weight_decay=0.01,
    load_best_model_at_end=True,
    eval_strategy="epoch",
    save_strategy="epoch",
    metric_for_best_model="f1",
    greater_is_better=True
)

train_dataset = TextDataset(train_encodings, train_labels)

val_dataset = TextDataset(val_encodings, val_labels)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics
)

trainer.train()

metrics = trainer.evaluate()
print("Final evaluation metrics:")
for k, v in metrics.items():
    print(f"{k}: {v}")

trainer.save_model("./roberta_classifier")
tokenizer.save_pretrained("./roberta_classifier")
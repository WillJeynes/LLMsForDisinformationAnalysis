from sklearn.utils import compute_class_weight
from torch.nn import CrossEntropyLoss
from transformers import Trainer, TrainingArguments, AutoTokenizer, AutoModelForSequenceClassification
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from collections import Counter
import sys
import csv
import numpy as np

NUM_CLASSES = 3
model_name = "distilbert/distilroberta-base" # Or MiniLM, or any other transformer model 

LABEL_PRIORITY = [
    ("PERFECT", 0),
    ("STORY", 1),
    ("NSPECIFIC", 2),
    ("REWORDING", 1),
    ("TINCORRECT", -1),
    ("DUPLICATE", -1),
    ("", 0),  # fallback to PERFECT
]

class WeightedTrainer(Trainer):
    def __init__(self, *args, class_weights=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        # print("DBG: Before forward")
        outputs = model(**inputs)
        # print("DBG: After forward")
        logits = outputs.get("logits")

        loss_fct = CrossEntropyLoss(
            weight=self.class_weights.to(logits.device).to(logits.dtype)
        )
        # loss_fct = CrossEntropyLoss()
        
        # print("DBG: Before loss")
        loss = loss_fct(logits, labels)
        # loss.backward()
        # print("DBG: After loss")
        return (loss, outputs) if return_outputs else loss

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
        "f1": f1_score(labels, preds, average="weighted", zero_division=0),
        "precision": precision_score(labels, preds, average="weighted", zero_division=0),
        "recall": recall_score(labels, preds, average="weighted", zero_division=0),
    }

def main():
    torch.multiprocessing.set_start_method('fork')
    print("CUDA available:", torch.cuda.is_available())
    print("CUDA device count:", torch.cuda.device_count())
    print("Current device:", torch.cuda.current_device() if torch.cuda.is_available() else "CPU")
    texts, labels = load_dataset_from_csv("../../data/classify.csv")

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=NUM_CLASSES
    )

    print("Dataset size:", len(texts))
    print("Label distribution:")
    print(Counter(labels))
    
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels
    )


    class_weights = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(train_labels),
        y=train_labels
    )

    class_weights = torch.tensor(class_weights, dtype=torch.float)
    print("Class weights:", class_weights)

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
            # print(f"DBG: Loading item {idx}")
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
        learning_rate=2e-5,
        per_device_train_batch_size=32,
        # gradient_accumulation_steps=2,
        num_train_epochs=15,
        weight_decay=0.01,
        load_best_model_at_end=True,
        eval_strategy="epoch",
        save_strategy="epoch",
        metric_for_best_model="f1",
        greater_is_better=True,
        dataloader_num_workers=4,
        dataloader_pin_memory=True,
        # warmup_steps=100,
    )

    train_dataset = TextDataset(train_encodings, train_labels)

    val_dataset = TextDataset(val_encodings, val_labels)

    trainer = WeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        class_weights=class_weights
    )

    trainer.train()

    metrics = trainer.evaluate()
    print("Final evaluation metrics:")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    trainer.save_model("./roberta_distilled_classifier")
    tokenizer.save_pretrained("./roberta_distilled_classifier")



if __name__ == "__main__":
    main()
from sklearn.utils import compute_class_weight
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Seq2SeqTrainer, Seq2SeqTrainingArguments, DataCollatorForSeq2Seq
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from collections import Counter
import sys
import csv
import numpy as np

NUM_CLASSES = 3
model_name = "google/flan-t5-base"

INT_TO_LABEL = {
    0: "perfect",
    1: "story",
    2: "not specific",
}
LABEL_TO_INT = {v: k for k, v in INT_TO_LABEL.items()}

LABEL_PRIORITY = [
    ("PERFECT", 0),
    ("STORY", 1),
    ("NSPECIFIC", 2),
    ("REWORDING", 1),
    ("TINCORRECT", -1),
    ("DUPLICATE", -1),
    ("", 0),
]

def label_to_int(extra_info: str) -> int:
    if extra_info is None:
        extra_info = ""
    extra_info = extra_info.strip()
    if extra_info == "":
        for key, value in LABEL_PRIORITY:
            if key == "":
                return value
        raise ValueError("Empty extra_info but no empty mapping defined")
    tokens = set(extra_info.upper().split())
    for key, value in LABEL_PRIORITY:
        if key == "" :
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
            if label_int == -1:
                removed_rows += 1
                continue
            texts.append(text)
            labels.append(label_int)
    print(f"Loaded {len(texts)} samples (removed {removed_rows})")
    return texts, labels


def format_prompt(text: str) -> str:
    return (
        "Classify the following event into one of these categories: "
        "perfect, story, not specific.\n\n"
        f"Event: {text}\n\n"
        "Category:"
    )


def parse_generated_label(generated: str) -> int:
    generated = generated.strip().lower()
    for label_text, label_int in LABEL_TO_INT.items():
        if label_text in generated:
            return label_int
    print("invlid label:" +  generated)
    return -1  # unknown / unparseable output


class GenerativeTextDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels, tokenizer, max_input_length=256, max_target_length=8):
        self.tokenizer = tokenizer
        self.max_input_length = max_input_length
        self.max_target_length = max_target_length

        self.inputs = [format_prompt(t) for t in texts]
        # Convert integer labels to their text equivalents for the target sequence
        self.targets = [INT_TO_LABEL[l] for l in labels]
        self.int_labels = labels  # keep originals for metric computation

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, idx):
        model_inputs = self.tokenizer(
            self.inputs[idx],
            max_length=self.max_input_length,
            truncation=True,
            padding=False,
        )
        target_encoding = self.tokenizer(
            self.targets[idx],
            max_length=self.max_target_length,
            truncation=True,
            padding=False,
        )
        # Seq2Seq convention: labels use -100 to ignore padding tokens in loss
        labels = target_encoding["input_ids"]
        labels = [token if token != self.tokenizer.pad_token_id else -100 for token in labels]

        model_inputs["labels"] = labels
        return {k: torch.tensor(v) for k, v in model_inputs.items()}


def compute_metrics_generative(eval_pred, tokenizer):
    predictions, label_ids = eval_pred

    # Decode predictions 
    # Replace -100 in labels before decoding
    label_ids = np.where(label_ids != -100, label_ids, tokenizer.pad_token_id)

    decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(label_ids, skip_special_tokens=True)

    # Map decoded text back to integer labels
    pred_ints = [parse_generated_label(p) for p in decoded_preds]
    true_ints = [parse_generated_label(l) for l in decoded_labels]

    # Filter out any rows where parsing failed
    valid = [(p, t) for p, t in zip(pred_ints, true_ints) if t != -1]
    if not valid:
        return {"accuracy": 0.0, "f1": 0.0, "precision": 0.0, "recall": 0.0}

    preds_filtered, true_filtered = zip(*valid)

    return {
        "accuracy": accuracy_score(true_filtered, preds_filtered),
        "f1": f1_score(true_filtered, preds_filtered, average="weighted", zero_division=0),
        "precision": precision_score(true_filtered, preds_filtered, average="weighted", zero_division=0),
        "recall": recall_score(true_filtered, preds_filtered, average="weighted", zero_division=0),
    }


def main():
    torch.multiprocessing.set_start_method('spawn', force=True) 
    print("CUDA available:", torch.cuda.is_available())
    print("CUDA device count:", torch.cuda.device_count())

    texts, labels = load_dataset_from_csv("../../data/classify.csv")

    print("Dataset size:", len(texts))
    print("Label distribution:", Counter(labels))

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels,
        test_size=0.2,
        random_state=42,
        stratify=labels
    )

    train_dataset = GenerativeTextDataset(train_texts, train_labels, tokenizer)
    val_dataset = GenerativeTextDataset(val_texts, val_labels, tokenizer)

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        label_pad_token_id=-100,
    )

    training_args = Seq2SeqTrainingArguments(
        output_dir="./results",
        learning_rate=5e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=10,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        predict_with_generate=True,
        generation_max_length=8,
        dataloader_num_workers=0,
        dataloader_pin_memory=False,
        fp16=False,
        max_grad_norm=1.0,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=lambda ep: compute_metrics_generative(ep, tokenizer),
    )

    trainer.train()

    metrics = trainer.evaluate()
    print("\nFinal evaluation metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    trainer.save_model("./flan_classifier")
    tokenizer.save_pretrained("./flan_classifier")


if __name__ == "__main__":
    main()
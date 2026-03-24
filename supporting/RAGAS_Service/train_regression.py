from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.utils import compute_class_weight
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from collections import Counter
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import csv
import sys

NUM_CLASSES    = 3
EMBEDDING_MODEL = "all-mpnet-base-v2"
HIDDEN_DIM     = 256
DROPOUT        = 0.3
LEARNING_RATE  = 1e-3
WEIGHT_DECAY   = 1e-4
BATCH_SIZE     = 64
NUM_EPOCHS     = 30
PATIENCE       = 5

LABEL_PRIORITY = [
    ("PERFECT",    0),
    ("STORY",      1),
    ("NSPECIFIC",  2),
    ("REWORDING",  1),
    ("TINCORRECT", -1),
    ("DUPLICATE",  -1),
    ("",           0),   # fallback to PERFECT
]


def label_to_int(extra_info: str) -> int:
    if extra_info is None:
        extra_info = ""
    extra_info = extra_info.strip()

    if extra_info == "":
        for key, value in LABEL_PRIORITY:
            if key == "":
                return value
        raise ValueError("No empty-string fallback defined in LABEL_PRIORITY")

    tokens = set(extra_info.upper().split())
    for key, value in LABEL_PRIORITY:
        if key and key in tokens:
            return value

    raise ValueError(f"Unknown label content: '{extra_info}'")


def load_dataset_from_csv(path: str):
    texts, labels = [], []
    removed = 0

    with open(path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=1):
            try:
                label_int = label_to_int(row["extra_info"])
            except Exception as e:
                print(f"ERROR on line {i}: {row['extra_info']!r}")
                print(e)
                sys.exit(1)

            if label_int == -1:
                removed += 1
                continue

            texts.append(row["event"])
            labels.append(label_int)

    print(f"Loaded {len(texts)} samples  (removed {removed})")
    return texts, labels


class LogisticNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),   # raw logits – loss handles softmax
        )

    def forward(self, x):
        return self.net(x)


# ── Metrics ───────────────────────────────────────────────────────────────────

def evaluate(model, loader, device):
    model.eval()
    all_preds, all_labels = [], []

    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            logits = model(xb)
            preds  = logits.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(yb.cpu().numpy())

    return {
        "accuracy":  accuracy_score(all_labels, all_preds),
        "f1":        f1_score(all_labels, all_preds, average="weighted", zero_division=0),
        "precision": precision_score(all_labels, all_preds, average="weighted", zero_division=0),
        "recall":    recall_score(all_labels, all_preds, average="weighted", zero_division=0),
    }


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    texts, labels = load_dataset_from_csv("../../data/classify.csv")
    print("Label distribution:", Counter(labels))

    print(f"\nEncoding with '{EMBEDDING_MODEL}' …")
    encoder = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = encoder.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    input_dim = embeddings.shape[1]
    print(f"Embedding dim: {input_dim}")

    X_train, X_val, y_train, y_val = train_test_split(
        embeddings, labels, test_size=0.2, random_state=42, stratify=labels
    )

    class_weights = compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)
    weight_tensor  = torch.tensor(class_weights, dtype=torch.float).to(device)
    print("Class weights:", class_weights)

    def make_loader(X, y, shuffle=False):
        ds = TensorDataset(
            torch.tensor(X, dtype=torch.float32),
            torch.tensor(y, dtype=torch.long),
        )
        return DataLoader(ds, batch_size=BATCH_SIZE, shuffle=shuffle)

    train_loader = make_loader(X_train, y_train, shuffle=True)
    val_loader   = make_loader(X_val,   y_val,   shuffle=False)

    model     = LogisticNet(input_dim, HIDDEN_DIM, NUM_CLASSES, DROPOUT).to(device)
    criterion = nn.CrossEntropyLoss(weight=weight_tensor)
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

    best_f1       = 0.0
    best_state    = None
    epochs_no_imp = 0

    print("\n Training:")
    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        total_loss = 0.0

        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(yb)

        scheduler.step()
        avg_loss = total_loss / len(train_loader.dataset)
        val_metrics = evaluate(model, val_loader, device)

        print(
            f"Epoch {epoch:3d}/{NUM_EPOCHS} | "
            f"loss {avg_loss:.4f} | "
            f"val_acc {val_metrics['accuracy']:.4f} | "
            f"val_f1 {val_metrics['f1']:.4f}"
        )

        # Early stopping on weighted F1
        if val_metrics["f1"] > best_f1:
            best_f1    = val_metrics["f1"]
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            epochs_no_imp = 0
        else:
            epochs_no_imp += 1
            if epochs_no_imp >= PATIENCE:
                print(f"Early stopping at epoch {epoch} (no improvement for {PATIENCE} epochs)")
                break

    print("\n Final evaluation:")
    model.load_state_dict(best_state)
    final = evaluate(model, val_loader, device)
    for k, v in final.items():
        print(f"  {k}: {v:.4f}")

    torch.save(
        {
            "model_state":   best_state,
            "input_dim":     input_dim,
            "hidden_dim":    HIDDEN_DIM,
            "num_classes":   NUM_CLASSES,
            "dropout":       DROPOUT,
            "embedding_model": EMBEDDING_MODEL,
        },
        "logreg_classifier.pt"
    )
    print("\n Model saved to logreg_classifier.pt")


if __name__ == "__main__":
    main()
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI
import torch
import torch.nn as nn
from huggingface_hub import hf_hub_download
import os

app = FastAPI()

HF_REPO_ID = "WillJeynes/LLMsForDisinformationAnalysis-Regression"
MODEL_FILENAME = "logreg_classifier.pt"
CACHE_DIR = "./model_cache"


def load_checkpoint(repo_id: str, filename: str, cache_dir: str) -> dict:
    local_path = os.path.join(cache_dir, filename)
    if not os.path.exists(local_path):
        print(f"Downloading {filename} from {repo_id}...")
        os.makedirs(cache_dir, exist_ok=True)
        downloaded = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=cache_dir,
        )
        print(f"Saved to {downloaded}")
    else:
        print(f"Using cached model at {local_path}")
    return torch.load(local_path, map_location="cpu")


class LogisticNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x):
        return self.net(x)


checkpoint = load_checkpoint(HF_REPO_ID, MODEL_FILENAME, CACHE_DIR)

encoder = SentenceTransformer(checkpoint["embedding_model"])

model = LogisticNet(
    input_dim   = checkpoint["input_dim"],
    hidden_dim  = checkpoint["hidden_dim"],
    num_classes = checkpoint["num_classes"],
    dropout     = checkpoint["dropout"],
)
model.load_state_dict(checkpoint["model_state"])
model.eval()


class EvalRequest(BaseModel):
    answer: str


@app.post("/evaluate")
def evaluate(req: EvalRequest):
    embedding = encoder.encode(
        [req.answer],
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    x = torch.tensor(embedding, dtype=torch.float32)

    with torch.no_grad():
        logits = model(x)

    probs = torch.softmax(logits, dim=1)

    return {
        "probabilities": probs.cpu().numpy().tolist()
    }
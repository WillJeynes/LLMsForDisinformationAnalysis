from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI
import torch
import torch.nn as nn

app = FastAPI()

MODEL_PATH = "logreg_classifier.pt"

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


checkpoint = torch.load(MODEL_PATH, map_location="cpu")

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
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch

MODEL_PATH = "./roberta_classifier"

tokenizer = RobertaTokenizer.from_pretrained(MODEL_PATH)
model = RobertaForSequenceClassification.from_pretrained(MODEL_PATH)

text2 = "High-profile political downplaying of COVID-19 (examples: President Trump saying 'it will go away' in March–August 2020)"
text = "Multiple mirrored reuploads (2020–2023) put the clip on other channels with titles implying it was a genuine 1970s public information film."

inputs = tokenizer(
    text,
    return_tensors="pt",
    truncation=True,
    padding=True
)

model.eval()

with torch.no_grad():
    logits = model(**inputs).logits

probs = torch.softmax(logits, dim=1)
print(probs)
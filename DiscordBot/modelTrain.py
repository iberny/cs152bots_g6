import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import pandas as pd
import joblib
from datasets import Dataset
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, TrainingArguments, Trainer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

# Load and preprocess data
df = pd.read_csv("/Users/ricky/Desktop/CS152/suicide_risk_sentences_realistic.csv")
le = LabelEncoder()
df["label_id"] = le.fit_transform(df["label"])
joblib.dump(le, "label_encoder.pkl")
dataset = Dataset.from_pandas(df[["sentence", "label_id"]].rename(columns={"sentence": "text", "label_id": "label"}))
dataset = dataset.train_test_split(test_size=0.2)
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

def tokenize_function(example):
    return tokenizer(example["text"], padding="max_length", truncation=True)

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# ====== LOAD MODEL ======
num_labels = len(le.classes_)
model = DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=num_labels)
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
model.to(device)

training_args = TrainingArguments(
    output_dir="./results",
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    num_train_epochs=3,
    learning_rate=2e-5,
    weight_decay=0.01,
    logging_dir="./logs",
    no_cuda=True,
    eval_strategy="epoch",
    save_strategy="no"
)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = torch.argmax(torch.tensor(logits), dim=1)
    return {"accuracy": accuracy_score(labels, preds)}

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
    compute_metrics=compute_metrics
)
trainer.train()

model.save_pretrained("distilbert-risk-model")
tokenizer.save_pretrained("distilbert-risk-model")

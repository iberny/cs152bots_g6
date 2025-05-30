import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from sentence_transformers import SentenceTransformer
import torch
import joblib

class Predictor:
    def __init__(self):
        self.svm_model = joblib.load("Models/SVM/svm_model_bert.pkl")
        self.vectorizer = joblib.load("Models/tfidf_vectorizer.pkl")
        self.le = joblib.load("Models/SVM/label_encoder.pkl")
        self.bert_model = SentenceTransformer('all-MiniLM-L6-v2')

        # self.BERTmodel = DistilBertForSequenceClassification.from_pretrained("DistilBERTModel")
        # self.BERTtokenizer = DistilBertTokenizer.from_pretrained("DistilBERTModel")
        # self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # self.BERTmodel.to(self.device)
        # self.BERTmodel.eval()

    def simplePredict(self, text):
        if not isinstance(text, list):
            text = [text]
        X_new = self.vectorizer.transform(text)
        y_pred = self.svm_model.predict(X_new)
        predicted_labels = self.le.inverse_transform(y_pred)
        return(predicted_labels)

    def svmPredict(self,text):
        if not isinstance(text, list):
            text = [text]
        sentence_embeddings = self.bert_model.encode(text, convert_to_numpy=True)
        predictions = self.svm_model.predict(sentence_embeddings)
        predicted_labels = self.le.inverse_transform(predictions)
        return predicted_labels

        # Show results
        # for sentence, label in zip(sentences, predicted_labels):
        #     print(f"Sentence: {sentence}\nPredicted Label: {label}\n")

    def predict(self, text):
        inputs = self.BERTtokenizer(text, return_tensors="pt", padding=True, truncation=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.BERTmodel(**inputs)
            predicted_class_id = torch.argmax(outputs.logits, dim=1).item()
            predicted_label = self.le.inverse_transform([predicted_class_id])[0]
            return predicted_label
                            
def test():
    # Predict on new data
    new_sentences = ["I feel like giving up today.", "I'm doing better now.", "I don't want to keep on going", "I felt resilient after the breakup often but I’m staying strong.", "I loved the end of that movie"]
    X_new = vectorizer.transform(new_sentences)
    y_pred = svm_model.predict(X_new)
    predicted_labels = le.inverse_transform(y_pred)

    print(predicted_labels)

def main():
    predictor = Predictor()
    while True:
        text = input("Enter a sentence or enter to quit: ")
        if text == "":
            break
        result = predictor.svmPredict(text)
        print(result)

if __name__ == "__main__":
    main()
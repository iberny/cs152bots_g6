import joblib

class Predictor:
    def __init__(self):
        svm_model = joblib.load("Models/svm_model.pkl")
        vectorizer = joblib.load("Models/tfidf_vectorizer.pkl")
        le = joblib.load("Models/label_encoder.pkl")

    def predict(text):
        if not isinstance(text, list):
            text = [text]
        X_new = vectorizer.transform(text)
        y_pred = svm_model.predict(X_new)
        predicted_labels = le.inverse_transform(y_pred)
        return(predicted_labels)
                        
def test():
    # Predict on new data
    new_sentences = ["I feel like giving up today.", "I'm doing better now.", "I don't want to keep on going", "I felt resilient after the breakup often but I’m staying strong.", "I loved the end of that movie"]
    X_new = vectorizer.transform(new_sentences)
    y_pred = svm_model.predict(X_new)
    predicted_labels = le.inverse_transform(y_pred)

    print(predicted_labels)

def main():
    svm_model = joblib.load("Models/svm_model.pkl")
    vectorizer = joblib.load("Models/tfidf_vectorizer.pkl")
    le = joblib.load("Models/label_encoder.pkl")
    while True:
        text = input("Enter a sentence or enter to quit: ")
        if text == "":
            break
        X_new = vectorizer.transform([text])
        y_pred = svm_model.predict(X_new)
        predicted_labels = le.inverse_transform(y_pred)
        print(predicted_labels)

if __name__ == "__main__":
    main()
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Load your dataset
df = pd.read_csv("/Users/ricky/Desktop/SD.csv", usecols=['sentence', 'label'])  # Replace with your filename

# Encode labels
le = LabelEncoder()
df['label_encoded'] = le.fit_transform(df['label'])

# Split the data
X_train, X_test, y_train, y_test = train_test_split(
    df['sentence'], df['label_encoded'], test_size=0.2, stratify=df['label_encoded'], random_state=42
)

# Drop rows with missing sentence data and realign labels
train_df = pd.DataFrame({'sentence': X_train, 'label': y_train})
train_df = train_df.dropna()

X_train = train_df['sentence'].astype(str)
y_train = train_df['label']

test_df = pd.DataFrame({'sentence': X_test, 'label': y_test})
test_df = test_df.dropna()

X_test = test_df['sentence'].astype(str)
y_test = test_df['label']

# TF-IDF vectorizer
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000, ngram_range=(1, 3))
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Train SVM
svm_model = SVC(C=0.2, kernel='linear', probability=True, verbose=True)
svm_model.fit(X_train_tfidf, y_train)

# Predict and evaluate
y_pred = svm_model.predict(X_test_tfidf)

print("Classification Report:\n")
print(classification_report(y_test, y_pred, target_names=le.classes_))

print("Confusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

joblib.dump(svm_model, "svm_model.pkl")

joblib.dump(vectorizer, "tfidf_vectorizer.pkl")

joblib.dump(le, "label_encoder.pkl")

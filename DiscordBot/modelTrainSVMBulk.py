import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from sentence_transformers import SentenceTransformer
from numpy import unique

# Load your dataset
df = pd.read_csv("/Users/ricky/Desktop/Improved.csv", usecols=['sentence', 'label'])  # Replace with your actual file path

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

# Load BERT sentence embedding model
bert_model = SentenceTransformer('all-MiniLM-L6-v2')

# Convert sentences into embeddings
X_train_embeddings = bert_model.encode(X_train.tolist(), convert_to_numpy=True)
X_test_embeddings = bert_model.encode(X_test.tolist(), convert_to_numpy=True)


# Train SVM on BERT embeddings
svm_model = SVC(C=0.025, kernel='linear', probability=True, verbose=True)
svm_model.fit(X_train_embeddings, y_train)

joblib.dump(svm_model, "svm_model_bert.pkl")
joblib.dump(le, "label_encoder.pkl")
# Predict and evaluate
y_pred = svm_model.predict(X_test_embeddings)

labels_present = sorted(unique(y_test))
print(classification_report(y_test, y_pred, labels=labels_present, target_names=le.inverse_transform(labels_present)))


print("Classification Report:\n")
print(classification_report(y_test, y_pred, target_names=le.classes_))

print("Confusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

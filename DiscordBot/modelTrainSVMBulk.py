import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from sklearn.model_selection import GridSearchCV
from sentence_transformers import SentenceTransformer
from numpy import unique

# Load your dataset
df = pd.read_csv("/Users/ricky/Desktop/Updated.csv", usecols=['sentence', 'label'])  # Replace with your actual file path

# Encode labels
le = LabelEncoder()
df['label_encoded'] = le.fit_transform(df['label'])

# Split the data
X_train, X_test, y_train, y_test = train_test_split(
    df['sentence'], df['label_encoded'], test_size=0.12, stratify=df['label_encoded'], random_state=42
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
svm_model = SVC(C=0.005, kernel='linear', probability=True, verbose=True)
param_grid = {
    'C': [0.001, 0.005, 0.01, 0.1, 1.0, 10]
}
grid_search = GridSearchCV(svm_model, param_grid, cv=5, scoring='f1_macro', verbose=2, n_jobs=-1)

grid_search.fit(X_train_embeddings, y_train)

# joblib.dump(svm_model, "svm_model_bert.pkl")
# joblib.dump(le, "label_encoder.pkl")

print("Best parameters found:", grid_search.best_params_)
print("Best CV score:", grid_search.best_score_)

# Save best model
joblib.dump(grid_search.best_estimator_, "svm_model_bert_best.pkl")

# Predict using best model
y_pred = grid_search.best_estimator_.predict(X_test_embeddings)

# Evaluation
print("Classification Report:\n")
print(classification_report(y_test, y_pred, target_names=le.classes_))

print("Confusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

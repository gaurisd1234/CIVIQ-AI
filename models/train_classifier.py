from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle

# Sample training data (small but explainable)
texts = [
    "Garbage overflowing near bus stop",
    "Waste not collected for days",
    "Water leakage near school",
    "No water supply in my area",
    "Potholes on main road",
    "Road damaged after rain",
    "Power cut since morning",
    "Electricity fluctuation issue"
]

labels = [
    "garbage",
    "garbage",
    "water",
    "water",
    "road",
    "road",
    "electricity",
    "electricity"
]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

model = LogisticRegression()
model.fit(X, labels)

# Save model & vectorizer
with open("classifier.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("Model training complete and saved.")

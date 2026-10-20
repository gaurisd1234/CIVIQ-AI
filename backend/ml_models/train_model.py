import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

data = [
    ("Garbage dumped near residential area", "garbage"),
    ("Overflowing garbage bins causing bad smell", "garbage"),
    ("Drainage water overflowing on road", "drainage"),
    ("Blocked drainage causing flooding", "drainage"),
    ("Large potholes on main road", "road"),
    ("Street lights not working at night", "streetlight"),
    ("Water leakage from pipeline", "water"),
    ("Noise pollution late night", "other"),
]

texts = [d[0] for d in data]
labels = [d[1] for d in data]

vectorizer = TfidfVectorizer(stop_words="english")
X = vectorizer.fit_transform(texts)

model = LogisticRegression(max_iter=1000)
model.fit(X, labels)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "classifier.pkl"), "wb") as f:
    pickle.dump(model, f)

with open(os.path.join(BASE_DIR, "vectorizer.pkl"), "wb") as f:
    pickle.dump(vectorizer, f)

print("Model trained successfully")
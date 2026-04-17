import joblib
from feature_extractor import extract_url_features, features_to_frame

model = joblib.load("models/rf_model.pkl")   # or "rf_model.pkl" if you moved it

for url in [
    "https://www.google.com",
    "http://secure-login.paypa1-verify-account.com/update",
    "http://192.168.0.14/bank/login?user=admin",
]:
    X = features_to_frame(extract_url_features(url))
    print(url)
    print("classes_:", model.classes_)
    print("predict:", model.predict(X)[0])
    print("predict_proba:", model.predict_proba(X)[0])
    print()
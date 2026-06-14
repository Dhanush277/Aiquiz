import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, learning_curve
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

from ml.dataset import generate_synthetic_dataset

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '..', 'scaler.pkl')
CM_PATH = os.path.join(os.path.dirname(__file__), '..', 'confusion_matrix.png')
LC_PATH = os.path.join(os.path.dirname(__file__), '..', 'learning_curve.png')
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset.csv')

def train_and_save_model():
    if not os.path.exists(DATA_PATH):
        generate_synthetic_dataset(filename='dataset.csv')
        
    df = pd.read_csv(DATA_PATH)
    
    # Features & Target
    X = df[['score', 'accuracy', 'average_response_time', 'questions_attempted']]
    y = df['performance_category']
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Logistic Regression
    # Using 'saga' solver as it's good for multiclass and standard scaling
    model = LogisticRegression(multi_class='multinomial', solver='saga', max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    print("Classification Report:\n", classification_report(y_test, y_pred))
    
    # Save Model and Scaler
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"Model saved to {MODEL_PATH}")
    
    # Plot Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=model.classes_, yticklabels=model.classes_)
    plt.title('Confusion Matrix - Logistic Regression')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(CM_PATH)
    plt.close()
    
    # Plot Learning Curve
    train_sizes, train_scores, test_scores = learning_curve(
        model, X_train_scaled, y_train, cv=5, n_jobs=-1, 
        train_sizes=np.linspace(.1, 1.0, 5)
    )
    
    train_scores_mean = np.mean(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    
    plt.figure(figsize=(8, 6))
    plt.plot(train_sizes, train_scores_mean, 'o-', color="r", label="Training score")
    plt.plot(train_sizes, test_scores_mean, 'o-', color="g", label="Cross-validation score")
    plt.title("Learning Curve - Logistic Regression")
    plt.xlabel("Training examples")
    plt.ylabel("Score")
    plt.legend(loc="best")
    plt.grid()
    plt.tight_layout()
    plt.savefig(LC_PATH)
    plt.close()

def ensure_model_trained():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        print("Training model for the first time...")
        train_and_save_model()

def predict_performance(score, accuracy, response_time, questions_attempted):
    ensure_model_trained()
    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        
        features = np.array([[score, accuracy, response_time, questions_attempted]])
        features_scaled = scaler.transform(features)
        
        prediction = model.predict(features_scaled)
        return prediction[0]
    except Exception as e:
        print(f"Prediction error: {e}")
        return "Average Performer" # safe fallback

if __name__ == '__main__':
    train_and_save_model()

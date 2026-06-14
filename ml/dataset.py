import pandas as pd
import numpy as np
import os

def generate_synthetic_dataset(filename="dataset.csv", num_records=5000):
    np.random.seed(42)
    
    # Features:
    # 1. score (0-1000)
    # 2. accuracy (0-100)
    # 3. average_response_time (1-30 seconds)
    # 4. questions_attempted (1-100)
    
    # We create synthetic distributions based on expected profiles
    
    # High Performers (30%): High score, High accuracy, low/medium response time
    n_high = int(num_records * 0.3)
    high_acc = np.random.normal(85, 10, n_high).clip(60, 100)
    high_time = np.random.normal(12, 4, n_high).clip(5, 25)
    high_att = np.random.randint(20, 50, n_high)
    high_score = high_att * 10 * (high_acc / 100) + np.random.normal(50, 20, n_high)
    
    # Average Performers (50%): Medium score, Medium accuracy, medium response time
    n_avg = int(num_records * 0.5)
    avg_acc = np.random.normal(55, 15, n_avg).clip(30, 75)
    avg_time = np.random.normal(18, 5, n_avg).clip(10, 30)
    avg_att = np.random.randint(15, 45, n_avg)
    avg_score = avg_att * 10 * (avg_acc / 100)
    
    # Low Performers (20%): Low score, Low accuracy, high response time
    n_low = num_records - n_high - n_avg
    low_acc = np.random.normal(30, 15, n_low).clip(0, 50)
    low_time = np.random.normal(25, 5, n_low).clip(15, 30)
    low_att = np.random.randint(5, 30, n_low)
    low_score = low_att * 10 * (low_acc / 100)
    
    scores = np.concatenate([high_score, avg_score, low_score])
    accuracies = np.concatenate([high_acc, avg_acc, low_acc])
    times = np.concatenate([high_time, avg_time, low_time])
    attempts = np.concatenate([high_att, avg_att, low_att])
    
    labels = ['High Performer'] * n_high + ['Average Performer'] * n_avg + ['Low Performer'] * n_low
    
    df = pd.DataFrame({
        'score': np.round(scores),
        'accuracy': np.round(accuracies, 2),
        'average_response_time': np.round(times, 2),
        'questions_attempted': attempts,
        'performance_category': labels
    })
    
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', filename)
    df.to_csv(file_path, index=False)
    print(f"Synthetic dataset generated at {file_path}")
    return file_path

if __name__ == '__main__':
    generate_synthetic_dataset()

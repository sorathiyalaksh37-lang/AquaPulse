import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.threshold = -0.1
        
    def train_model(self, data_path=None):
        """Train Isolation Forest model on historical data"""
        
        # Generate synthetic training data if no real data exists
        if data_path is None or not os.path.exists(data_path):
            print("Generating synthetic training data...")
            train_data = self.generate_synthetic_data()
        else:
            train_data = pd.read_csv(data_path)
        
        # Select features for training
        features = ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen']
        X = train_data[features].values
        
        # Scale the features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.model.fit(X_scaled)
        
        # Save model
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.model, 'models/anomaly_detector.pkl')
        joblib.dump(self.scaler, 'models/scaler.pkl')
        
        print("Model training complete!")
        
    def generate_synthetic_data(self, n_samples=1000):
        """Generate synthetic training data"""
        np.random.seed(42)
        
        data = {
            'pH': np.random.normal(7.2, 0.5, n_samples),
            'tds': np.random.normal(250, 50, n_samples),
            'turbidity': np.random.normal(1.5, 0.5, n_samples),
            'temperature': np.random.normal(25, 3, n_samples),
            'conductivity': np.random.normal(500, 100, n_samples),
            'dissolved_oxygen': np.random.normal(8.5, 1, n_samples)
        }
        
        # Add some anomalies
        anomaly_indices = np.random.choice(n_samples, size=int(n_samples*0.1), replace=False)
        for idx in anomaly_indices:
            if np.random.random() > 0.5:
                data['pH'][idx] = np.random.uniform(4, 6)
            else:
                data['turbidity'][idx] = np.random.uniform(10, 25)
        
        return pd.DataFrame(data)
    
    def predict(self, reading):
        """Predict if a reading is anomalous"""
        if self.model is None or self.scaler is None:
            # Load saved model if available
            if os.path.exists('models/anomaly_detector.pkl'):
                self.model = joblib.load('models/anomaly_detector.pkl')
                self.scaler = joblib.load('models/scaler.pkl')
            else:
                self.train_model()
        
        # Extract features
        features = ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen']
        X = np.array([reading['parameters'][f] for f in features]).reshape(1, -1)
        
        # Scale
        X_scaled = self.scaler.transform(X)
        
        # Predict (1 = normal, -1 = anomaly)
        prediction = self.model.predict(X_scaled)[0]
        
        return prediction == -1

# Singleton detector
detector = AnomalyDetector()

# Train model on startup
try:
    detector.train_model()
except Exception as e:
    print(f"Model training warning: {e}")

if __name__ == "__main__":
    # Test anomaly detection
    from data_simulator import simulator
    
    print("Testing anomaly detection...")
    for i in range(20):
        reading = simulator.get_sensor_data()
        is_anomaly = detector.predict(reading)
        print(f"Reading {i+1}: Overall Status: {reading['overall_status']}, Anomaly: {is_anomaly}")

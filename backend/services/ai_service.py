"""AI/ML Service for predictions and analytics"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import joblib
import os
from datetime import datetime, timedelta

try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, Conv1D, MaxPooling1D, Flatten
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. LSTM models will not work.")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: XGBoost not available. Maintenance prediction will use fallback.")

class AIService:
    """AI/ML service for water quality predictions and analytics"""
    
    def __init__(self):
        self.models_dir = 'models/ai'
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Model instances
        self.lstm_model = None
        self.cnn_bilstm_model = None
        self.isolation_forest = None
        self.xgboost_model = None
        self.scaler = None
        self.parameter_scalers = {}
        
        # Parameters to monitor
        self.parameters = ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen']
        
        # Load existing models
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models if they exist"""
        try:
            # Load Isolation Forest
            if_path = os.path.join(self.models_dir, 'isolation_forest.pkl')
            if os.path.exists(if_path):
                self.isolation_forest = joblib.load(if_path)
                print("Loaded Isolation Forest model")
            
            # Load scaler
            scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                print("Loaded scaler")
            
            # Load LSTM model
            if TENSORFLOW_AVAILABLE:
                lstm_path = os.path.join(self.models_dir, 'lstm_model.h5')
                if os.path.exists(lstm_path):
                    self.lstm_model = load_model(lstm_path)
                    print("Loaded LSTM model")
                
                # Load CNN-BiLSTM model
                cnn_bilstm_path = os.path.join(self.models_dir, 'cnn_bilstm_model.h5')
                if os.path.exists(cnn_bilstm_path):
                    self.cnn_bilstm_model = load_model(cnn_bilstm_path)
                    print("Loaded CNN-BiLSTM model")
            
            # Load XGBoost model
            if XGBOOST_AVAILABLE:
                xgb_path = os.path.join(self.models_dir, 'xgboost_maintenance.pkl')
                if os.path.exists(xgb_path):
                    self.xgboost_model = joblib.load(xgb_path)
                    print("Loaded XGBoost model")
            
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def train_isolation_forest(self, data):
        """Train Isolation Forest for anomaly detection"""
        try:
            if len(data) < 100:
                return False, "Insufficient data for training (need at least 100 samples)"
            
            # Extract features
            X = data[self.parameters].values
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest
            self.isolation_forest = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100,
                max_samples='auto',
                n_jobs=-1
            )
            self.isolation_forest.fit(X_scaled)
            
            # Save models
            joblib.dump(self.isolation_forest, os.path.join(self.models_dir, 'isolation_forest.pkl'))
            joblib.dump(self.scaler, os.path.join(self.models_dir, 'scaler.pkl'))
            
            return True, "Isolation Forest trained successfully"
            
        except Exception as e:
            return False, f"Training failed: {str(e)}"
    
    def detect_anomaly(self, reading):
        """Detect anomaly in a reading"""
        try:
            if self.isolation_forest is None or self.scaler is None:
                return False, 0.0, "Models not loaded"
            
            # Extract features
            features = np.array([[
                reading['pH'], reading['tds'], reading['turbidity'],
                reading['temperature'], reading['conductivity'], reading['dissolved_oxygen']
            ]])
            
            # Scale
            features_scaled = self.scaler.transform(features)
            
            # Predict
            prediction = self.isolation_forest.predict(features_scaled)[0]
            anomaly_score = self.isolation_forest.score_samples(features_scaled)[0]
            
            is_anomaly = prediction == -1
            
            # Normalize score to 0-1 range (more negative = more anomalous)
            normalized_score = abs(anomaly_score) if is_anomaly else 0.0
            
            return is_anomaly, normalized_score, "Success"
            
        except Exception as e:
            return False, 0.0, f"Detection failed: {str(e)}"
    
    def build_lstm_model(self, input_shape):
        """Build LSTM model for time series forecasting"""
        if not TENSORFLOW_AVAILABLE:
            return None
        
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(64, return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(6)  # Output for all 6 parameters
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def build_cnn_bilstm_model(self, input_shape):
        """Build CNN-BiLSTM model for anomaly detection"""
        if not TENSORFLOW_AVAILABLE:
            return None
        
        model = Sequential([
            Conv1D(64, 3, activation='relu', input_shape=input_shape),
            MaxPooling1D(2),
            Bidirectional(LSTM(64, return_sequences=True)),
            Dropout(0.3),
            Bidirectional(LSTM(32)),
            Dropout(0.3),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid')  # Binary classification
        ])
        
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model
    
    def forecast_24h(self, historical_data, parameter=None):
        """Forecast next 24 hours using LSTM"""
        try:
            if not TENSORFLOW_AVAILABLE:
                return self.simple_forecast(historical_data, parameter)
            
            if len(historical_data) < 24:
                return None, "Insufficient data for forecasting"
            
            # Use simple moving average if LSTM not trained
            if self.lstm_model is None:
                return self.simple_forecast(historical_data, parameter)
            
            # Prepare data for LSTM
            # This is a simplified version - in production, you'd need proper sequence preparation
            df = pd.DataFrame(historical_data)
            
            if parameter:
                # Forecast single parameter
                values = df[parameter].values[-24:]
                # Simple extrapolation
                trend = np.mean(np.diff(values[-5:]))
                forecast = [values[-1] + trend * i for i in range(1, 25)]
                
                return {
                    'parameter': parameter,
                    'forecast': forecast,
                    'confidence_lower': [f * 0.95 for f in forecast],
                    'confidence_upper': [f * 1.05 for f in forecast],
                    'method': 'trend_extrapolation'
                }, None
            else:
                # Forecast all parameters
                forecasts = {}
                for param in self.parameters:
                    values = df[param].values[-24:]
                    trend = np.mean(np.diff(values[-5:]))
                    forecast = [values[-1] + trend * i for i in range(1, 25)]
                    
                    forecasts[param] = {
                        'forecast': forecast,
                        'confidence_lower': [f * 0.95 for f in forecast],
                        'confidence_upper': [f * 1.05 for f in forecast]
                    }
                
                return forecasts, None
            
        except Exception as e:
            return None, f"Forecasting failed: {str(e)}"
    
    def simple_forecast(self, historical_data, parameter=None):
        """Simple forecasting using moving average and trend"""
        try:
            df = pd.DataFrame(historical_data)
            
            if parameter:
                values = df[parameter].values[-24:]
                
                # Calculate trend
                trend = np.mean(np.diff(values[-5:]))
                
                # Generate forecast
                forecast = []
                last_value = values[-1]
                for i in range(1, 25):
                    next_value = last_value + (trend * i)
                    forecast.append(float(next_value))
                
                return {
                    'parameter': parameter,
                    'forecast': forecast,
                    'confidence_lower': [f * 0.95 for f in forecast],
                    'confidence_upper': [f * 1.05 for f in forecast],
                    'method': 'moving_average_trend'
                }, None
            else:
                forecasts = {}
                for param in self.parameters:
                    values = df[param].values[-24:]
                    trend = np.mean(np.diff(values[-5:]))
                    last_value = values[-1]
                    
                    forecast = [float(last_value + (trend * i)) for i in range(1, 25)]
                    
                    forecasts[param] = {
                        'forecast': forecast,
                        'confidence_lower': [f * 0.95 for f in forecast],
                        'confidence_upper': [f * 1.05 for f in forecast]
                    }
                
                return forecasts, None
                
        except Exception as e:
            return None, f"Forecasting failed: {str(e)}"
    
    def predict_maintenance(self, equipment_data):
        """Predict equipment maintenance needs"""
        try:
            # Simple rule-based prediction if XGBoost not available
            predictions = {}
            
            for equipment, data in equipment_data.items():
                health = data.get('health', 100)
                last_maintenance_days = data.get('last_maintenance_days', 0)
                usage_hours = data.get('usage_hours', 0)
                
                # Calculate degradation rate
                degradation_rate = (100 - health) / max(last_maintenance_days, 1)
                
                # Predict days until maintenance needed (health < 70)
                if health > 70:
                    days_until_maintenance = max(1, int((health - 70) / max(degradation_rate, 0.1)))
                else:
                    days_until_maintenance = 0
                
                # Determine priority
                if health < 50:
                    priority = 'critical'
                elif health < 70:
                    priority = 'high'
                elif health < 85:
                    priority = 'medium'
                else:
                    priority = 'low'
                
                predictions[equipment] = {
                    'current_health': health,
                    'days_until_maintenance': days_until_maintenance,
                    'estimated_failure_date': (datetime.now() + timedelta(days=days_until_maintenance)).isoformat(),
                    'priority': priority,
                    'recommendation': self._get_maintenance_recommendation(equipment, health, days_until_maintenance)
                }
            
            return predictions, None
            
        except Exception as e:
            return None, f"Maintenance prediction failed: {str(e)}"
    
    def _get_maintenance_recommendation(self, equipment, health, days):
        """Get maintenance recommendation based on equipment condition"""
        if health < 50:
            return f"Immediate maintenance required for {equipment}. Risk of failure."
        elif health < 70:
            return f"Schedule maintenance for {equipment} within {days} days."
        elif health < 85:
            return f"Plan routine maintenance for {equipment} in approximately {days} days."
        else:
            return f"{equipment} is in good condition. Next check in {days} days."
    
    def analyze_trends(self, historical_data, period='monthly'):
        """Analyze trends in water quality data"""
        try:
            df = pd.DataFrame(historical_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Group by period
            if period == 'monthly':
                df['period'] = df['timestamp'].dt.to_period('M')
            elif period == 'weekly':
                df['period'] = df['timestamp'].dt.to_period('W')
            else:  # daily
                df['period'] = df['timestamp'].dt.to_period('D')
            
            # Calculate statistics for each parameter
            trends = {}
            for param in self.parameters:
                grouped = df.groupby('period')[param].agg(['mean', 'min', 'max', 'std'])
                
                trends[param] = {
                    'periods': [str(p) for p in grouped.index],
                    'mean': grouped['mean'].tolist(),
                    'min': grouped['min'].tolist(),
                    'max': grouped['max'].tolist(),
                    'std': grouped['std'].tolist(),
                    'trend_direction': self._calculate_trend_direction(grouped['mean'].values)
                }
            
            return trends, None
            
        except Exception as e:
            return None, f"Trend analysis failed: {str(e)}"
    
    def _calculate_trend_direction(self, values):
        """Calculate overall trend direction"""
        if len(values) < 2:
            return 'stable'
        
        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if abs(slope) < 0.01:
            return 'stable'
        elif slope > 0:
            return 'increasing'
        else:
            return 'decreasing'
    
    def get_model_info(self):
        """Get information about loaded models"""
        return {
            'isolation_forest': self.isolation_forest is not None,
            'lstm_model': self.lstm_model is not None,
            'cnn_bilstm_model': self.cnn_bilstm_model is not None,
            'xgboost_model': self.xgboost_model is not None,
            'scaler': self.scaler is not None,
            'tensorflow_available': TENSORFLOW_AVAILABLE,
            'xgboost_available': XGBOOST_AVAILABLE
        }

# Singleton instance
ai_service = AIService()

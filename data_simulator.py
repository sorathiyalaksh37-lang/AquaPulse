import random
import json
import time
from datetime import datetime
import numpy as np

class WaterQualitySimulator:
    def __init__(self):
        # Safe ranges for drinking water (BIS 10500:2012)
        self.safe_ranges = {
            'pH': {'min': 6.5, 'max': 8.5, 'unit': ''},
            'tds': {'min': 0, 'max': 500, 'unit': 'ppm'},
            'turbidity': {'min': 0, 'max': 5, 'unit': 'NTU'},
            'temperature': {'min': 15, 'max': 35, 'unit': '°C'},
            'conductivity': {'min': 0, 'max': 1000, 'unit': 'µS/cm'},
            'dissolved_oxygen': {'min': 5, 'max': 14, 'unit': 'mg/L'}
        }
        
        # Current values (starting at safe levels)
        self.current_values = {
            'pH': 7.2,
            'tds': 250,
            'turbidity': 1.5,
            'temperature': 25,
            'conductivity': 500,
            'dissolved_oxygen': 8.5
        }
        
        self.contamination_event = False
        self.event_counter = 0
        
    def generate_reading(self):
        """Generate a realistic water quality reading"""
        
        # Random fluctuation (normal operation)
        fluctuation = {
            'pH': random.uniform(-0.05, 0.05),
            'tds': random.uniform(-5, 5),
            'turbidity': random.uniform(-0.1, 0.1),
            'temperature': random.uniform(-0.5, 0.5),
            'conductivity': random.uniform(-10, 10),
            'dissolved_oxygen': random.uniform(-0.2, 0.2)
        }
        
        # Simulate contamination events (every 30-40 readings)
        if random.randint(1, 40) == 1 and not self.contamination_event:
            self.contamination_event = True
            self.event_counter = 0
            # Severe contamination simulation
            self.current_values['pH'] = random.uniform(4.5, 5.5)  # Acidic
            self.current_values['turbidity'] = random.uniform(15, 25)  # Very turbid
            self.current_values['tds'] = random.uniform(800, 1200)  # High TDS
        
        # Recover from contamination
        if self.contamination_event:
            self.event_counter += 1
            # Gradually return to normal
            for key in self.current_values:
                if key == 'pH':
                    self.current_values[key] += (7.2 - self.current_values[key]) * 0.05
                elif key == 'turbidity':
                    self.current_values[key] += (1.5 - self.current_values[key]) * 0.05
                elif key == 'tds':
                    self.current_values[key] += (250 - self.current_values[key]) * 0.05
                else:
                    self.current_values[key] += fluctuation[key]
            
            if self.event_counter > 15:  # Recovery after 15 readings
                self.contamination_event = False
                self.event_counter = 0
                # Reset to normal
                self.current_values = {
                    'pH': 7.2,
                    'tds': 250,
                    'turbidity': 1.5,
                    'temperature': 25,
                    'conductivity': 500,
                    'dissolved_oxygen': 8.5
                }
        else:
            # Normal operation - apply random fluctuations
            for key in self.current_values:
                self.current_values[key] += fluctuation[key]
                # Keep within realistic ranges
                if key == 'pH':
                    self.current_values[key] = max(6.0, min(9.0, self.current_values[key]))
                elif key == 'tds':
                    self.current_values[key] = max(50, min(1500, self.current_values[key]))
                elif key == 'turbidity':
                    self.current_values[key] = max(0, min(30, self.current_values[key]))
                elif key == 'temperature':
                    self.current_values[key] = max(15, min(35, self.current_values[key]))
                elif key == 'conductivity':
                    self.current_values[key] = max(100, min(2000, self.current_values[key]))
                elif key == 'dissolved_oxygen':
                    self.current_values[key] = max(2, min(14, self.current_values[key]))
        
        # Create reading object
        reading = {
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                'pH': round(self.current_values['pH'], 2),
                'tds': round(self.current_values['tds'], 1),
                'turbidity': round(self.current_values['turbidity'], 2),
                'temperature': round(self.current_values['temperature'], 1),
                'conductivity': round(self.current_values['conductivity'], 1),
                'dissolved_oxygen': round(self.current_values['dissolved_oxygen'], 2)
            }
        }
        
        return reading
    
    def get_sensor_data(self):
        """Get current sensor reading with status"""
        reading = self.generate_reading()
        
        # Determine status for each parameter
        status = {}
        for param, value in reading['parameters'].items():
            safe = self.safe_ranges[param]
            if value < safe['min'] or value > safe['max']:
                status[param] = 'danger'
            elif value < safe['min'] * 1.1 or value > safe['max'] * 0.9:
                status[param] = 'warning'
            else:
                status[param] = 'safe'
        
        # Overall status
        if 'danger' in status.values():
            overall = 'Unsafe'
        elif 'warning' in status.values():
            overall = 'Caution'
        else:
            overall = 'Safe'
        
        reading['status'] = status
        reading['overall_status'] = overall
        
        return reading

# Singleton instance
simulator = WaterQualitySimulator()

if __name__ == "__main__":
    # Test the simulator
    for i in range(5):
        data = simulator.get_sensor_data()
        print(json.dumps(data, indent=2))
        time.sleep(1)
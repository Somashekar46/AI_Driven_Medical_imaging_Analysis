"""
Test script to verify the /records/save endpoint works
"""
import requests
import json

# Test data
test_record = {
    "patient_name": "John Doe",
    "gender": "Male",
    "model": "rickets",
    "prediction": "Normal",
    "confidence": 0.95,
    "probabilities": {
        "Normal": 0.95,
        "Mild": 0.04,
        "Severe": 0.01
    }
}

# Make the request
try:
    response = requests.post(
        'http://localhost:8000/records/save',
        json=test_record,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test getting records
    print("\n--- Getting all records ---")
    response = requests.get('http://localhost:8000/records/all')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
except Exception as e:
    print(f"Error: {e}")

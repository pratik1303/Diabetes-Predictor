from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import joblib
from pymongo import MongoClient
#from dotenv import load_dotenv
import os
#load_dotenv()
# Load environment variables
MONGO_URI = os.getenv('MONGO_URI')

# Initialize Flask app
app = Flask(__name__)

# MongoDB configuration
# Load from environment variable
client = MongoClient(MONGO_URI)
db = client['diabetes_prediction']  # Database name
feedback_collection = db['feedback']  # Collection name

# Load pre-trained model and scaler
MODEL_PATH = 'models/rf_model.pkl'
SCALER_PATH = 'models/rf_scaler.pkl'

model = joblib.load(MODEL_PATH)  # Replace with actual model file path
scaler = joblib.load(SCALER_PATH)  # Replace with actual scaler file path

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # Collect user input from the form
    try:
        pregnancies = float(request.form['Pregnancies'])
        glucose = float(request.form['Glucose'])
        blood_pressure = float(request.form['BloodPressure'])
        skin_thickness = float(request.form['SkinThickness'])
        insulin = float(request.form['Insulin'])
        bmi = float(request.form['BMI'])
        diabetes_pedigree_function = float(request.form['DiabetesPedigreeFunction'])
        age = float(request.form['Age'])

        # Input validation with defined ranges
        if not (0 <= pregnancies <= 20):
            return "Invalid Pregnancies value. Must be between 0 and 20.", 400
        if not (0 <= glucose <= 200):
            return "Invalid Glucose value. Must be between 0 and 200.", 400
        if not (0 <= blood_pressure <= 140):
            return "Invalid Blood Pressure value. Must be between 0 and 140.", 400
        if not (0 <= skin_thickness <= 99):
            return "Invalid Skin Thickness value. Must be between 0 and 99.", 400
        if not (0 <= insulin <= 900):
            return "Invalid Insulin value. Must be between 0 and 900.", 400
        if not (0 <= bmi <= 70):
            return "Invalid BMI value. Must be between 0 and 70.", 400
        if not (0 <= diabetes_pedigree_function <= 2.5):
            return "Invalid Diabetes Pedigree Function value. Must be between 0 and 2.5.", 400
        if not (0 <= age <= 110):
            return "Invalid Age value. Must be between 0 and 110.", 400

        # Prepare input data for prediction
        input_data = np.array([[pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree_function, age]])
        input_data_scaled = scaler.transform(input_data)

        # Predict using the model
        prediction = model.predict(input_data_scaled)
        result = "Diabetic" if prediction[0] == 1 else "Not Diabetic"

        # Render the result page with buttons for feedback
        return render_template('result.html', result=result, input_data=input_data.tolist())

    except Exception as e:
        return f"Error: {e}", 500


@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        # Get user feedback and input data from the form
        feedback = request.form['feedback']  # 'correct' or 'incorrect'
        input_data = request.form['input_data']  # Retrieve input data passed as hidden input

        # Parse input data string back into a Python list
        input_data = eval(input_data)

        # Save feedback, input data, and predicted label into MongoDB
        feedback_data = {
            'input_data': input_data,  # Store user inputs
            'predicted_label': int(request.form.get('label', 0)),  # Predicted label passed as hidden input
            'feedback': feedback  # User feedback: 'correct' or 'incorrect'
        }
        
        # Debug prints
        print(f"MONGO_URI: {MONGO_URI}")
        print(f"Feedback data: {feedback_data}")

        # Insert into MongoDB collection
        feedback_collection.insert_one(feedback_data)

        return render_template('feedback.html')
    except Exception as e:
        # Log any errors
        print(f"Error saving feedback: {str(e)}")
        return f"Error saving feedback: {str(e)}", 500




if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Dynamically assigned port for deployment
    app.run(host='0.0.0.0', port=port, debug=False)  # Disable debug in production

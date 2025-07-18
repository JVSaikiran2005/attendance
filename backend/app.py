# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import csv
import io

app = Flask(__name__)
# Enable CORS for all routes, essential for frontend-backend communication
# In production, you might want to restrict this to your specific frontend domain.
CORS(app) 

# Initialize Firebase Admin SDK
# Ensure serviceAccountKey.json is in the same directory as this app.py
try:
    # Load the service account key JSON file
    # This file contains credentials that grant your backend administrative access to Firestore.
    cred = credentials.Certificate("serviceAccountKey.json")
    # Initialize the Firebase app
    firebase_admin.initialize_app(cred)
    # Get a Firestore client
    db = firestore.client()
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"ERROR: Firebase Admin SDK initialization failed: {e}")
    print("Please ensure 'serviceAccountKey.json' is in the 'backend' folder and is valid.")
    print("You can generate it from Firebase Console -> Project settings -> Service accounts.")
    # Exit the application if Firebase Admin SDK initialization fails, as it's critical.
    exit() 

# Get the Firebase Project ID. This will be used in Firestore paths to match frontend.
# This ID comes from your serviceAccountKey.json and should match your frontend's projectId.
PROJECT_ID = firebase_admin.get_app().project_id
print(f"Using Firebase Project ID as appId for Firestore paths: {PROJECT_ID}")


@app.route('/')
def hello_world():
    """Simple route to confirm the Flask backend is running."""
    return 'Flask Backend for Attendance System is running!'

@app.route('/api/students/upload', methods=['POST'])
def upload_students():
    """
    API endpoint to upload student data from a CSV file to Firestore.
    The CSV should have headers: studentId,rollNumber,name,branch,department,section
    """
    # Check if a file was sent in the request
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    
    # Check if a file was actually selected
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a CSV"}), 400

    try:
        # Read the CSV file content
        # io.TextIOWrapper handles decoding the file stream
        stream = io.TextIOWrapper(file.stream, encoding='utf-8')
        csv_reader = csv.reader(stream)
        
        # Read headers from the first row of the CSV
        headers = [h.strip() for h in next(csv_reader)] 

        # Define expected headers for validation
        expected_headers = ['studentId', 'rollNumber', 'name', 'branch', 'department', 'section']
        # Check if all expected headers are present in the CSV
        if not all(h in headers for h in expected_headers):
            return jsonify({"error": f"CSV missing required headers. Expected: {', '.join(expected_headers)}"}), 400

        students_to_add = []
        for row_num, row in enumerate(csv_reader):
            if not row: # Skip empty rows
                continue
            # Ensure row has enough columns to match headers
            if len(row) < len(headers):
                print(f"Skipping row {row_num + 2} due to insufficient columns: {row}")
                continue

            student_data = {}
            # Map CSV row values to dictionary using headers
            for i, header in enumerate(headers):
                student_data[header] = row[i].strip()
            
            # Basic validation: ensure all expected fields have data
            if all(student_data.get(h) for h in expected_headers):
                students_to_add.append(student_data)
            else:
                print(f"Skipping row {row_num + 2} due to missing data in required fields: {student_data}")

        if not students_to_add:
            return jsonify({"error": "No valid student data found in CSV."}), 400

        # Use Firestore batch writes for efficiency when adding multiple documents
        batch = db.batch()
        # Define the Firestore collection path for students
        students_collection_ref = db.collection(f'artifacts/{PROJECT_ID}/public/data/students')

        for student in students_to_add:
            student_id = student.get('studentId')
            if student_id:
                # Use studentId as the document ID for easy retrieval
                doc_ref = students_collection_ref.document(student_id)
                batch.set(doc_ref, student) # Use set() to create or overwrite
            else:
                print(f"Skipping student due to missing studentId: {student}")

        batch.commit() # Commit all batched writes
        return jsonify({"message": f"Successfully uploaded {len(students_to_add)} students!"}), 200

    except Exception as e:
        # Log the detailed error for backend debugging
        print(f"ERROR during student CSV upload: {e}")
        # Return a more generic error message to the frontend for security
        return jsonify({"error": "An internal server error occurred during student upload. Please try again."}), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    """
    API endpoint to retrieve all student data from Firestore.
    """
    try:
        # Define the Firestore collection path for students
        students_ref = db.collection(f'artifacts/{PROJECT_ID}/public/data/students')
        # Stream all documents from the collection
        docs = students_ref.stream()
        students_list = []
        for doc in docs:
            students_list.append(doc.to_dict()) # Convert each document to a dictionary
        return jsonify(students_list), 200
    except Exception as e:
        # Log the detailed error for backend debugging
        print(f"ERROR fetching students: {e}")
        # Return a more generic error message to the frontend for security
        return jsonify({"error": "An internal server error occurred while fetching student data. Please try again."}), 500

if __name__ == '__main__':
    # Run Flask app on port 5000.
    # debug=True enables reloader and debugger (useful for development).
    # host='0.0.0.0' makes it accessible from other devices on your network (optional, '127.0.0.1' for local only).
    app.run(debug=True, port=5000)

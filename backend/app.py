# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import csv
import io

app = Flask(__name__)
CORS(app) 

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"ERROR: Firebase Admin SDK initialization failed: {e}")
    print("Please ensure 'serviceAccountKey.json' is in the 'backend' folder and is valid.")
    exit() 

PROJECT_ID = firebase_admin.get_app().project_id
print(f"Using Firebase Project ID as appId for Firestore paths: {PROJECT_ID}")


@app.route('/')
def hello_world():
    return 'Flask Backend for Attendance System is running!'

@app.route('/api/students/upload', methods=['POST'])
def upload_students():
    """
    API endpoint to upload student data from a CSV file to Firestore.
    The CSV should have headers: studentId,rollNumber,name,branch,department,section,academicYear
    """
    if 'file' not in request.files:
        print("DEBUG: No 'file' part in request.files")
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    
    if file.filename == '':
        print("DEBUG: No selected file (filename is empty)")
        return jsonify({"error": "No selected file"}), 400
    
    if not file.filename.endswith('.csv'):
        print(f"DEBUG: Invalid file type: {file.filename}. Must be CSV.")
        return jsonify({"error": "File must be a CSV"}), 400

    try:
        stream = io.TextIOWrapper(file.stream, encoding='utf-8')
        csv_reader = csv.reader(stream)
        
        try:
            headers = [h.strip() for h in next(csv_reader)] 
            if not headers: # Check if headers row was empty after stripping
                 print("DEBUG: CSV file is empty or headers row is empty.")
                 return jsonify({"error": "CSV file is empty or contains no valid headers."}), 400
        except StopIteration:
            print("DEBUG: StopIteration - CSV file is empty or contains no headers.")
            return jsonify({"error": "CSV file is empty or contains no headers."}), 400

        # IMPORTANT: Updated expected headers to include academicYear
        expected_headers = ['studentId', 'rollNumber', 'name', 'branch', 'department', 'section', 'academicYear'] 
        
        missing_headers = [h for h in expected_headers if h not in headers]
        if missing_headers:
            print(f"DEBUG: CSV missing required headers: {', '.join(missing_headers)}. Found: {', '.join(headers)}")
            return jsonify({"error": f"CSV missing required headers: {', '.join(missing_headers)}. Please ensure all columns are present."}), 400

        students_to_add = []
        for row_num, row in enumerate(csv_reader):
            if not row or all(not cell.strip() for cell in row): # Skip entirely empty rows
                continue
            
            # Map CSV row values to dictionary using headers
            student_data = {}
            for i, header in enumerate(headers):
                if i < len(row): # Ensure index is within bounds of the row
                    student_data[header] = row[i].strip()
                else:
                    # Handle cases where rows might be shorter than headers
                    student_data[header] = "" 
            
            # Basic validation: ensure essential fields have data
            # Now includes academicYear in validation
            if not all(student_data.get(h) for h in ['studentId', 'rollNumber', 'name', 'branch', 'department', 'section', 'academicYear']):
                print(f"DEBUG: Skipping row {row_num + 2} due to missing data in essential fields: {student_data}")
                continue # Skip rows with incomplete essential data

            students_to_add.append(student_data)

        if not students_to_add:
            print("DEBUG: No valid student data found in CSV after processing.")
            return jsonify({"error": "No valid student data found in CSV. Ensure your CSV has data in all required columns."}), 400

        batch = db.batch()
        students_collection_ref = db.collection(f'artifacts/{PROJECT_ID}/public/data/students')

        for student in students_to_add:
            student_id = student.get('studentId')
            if student_id:
                doc_ref = students_collection_ref.document(student_id)
                batch.set(doc_ref, student) 
            else:
                print(f"DEBUG: Skipping student due to missing studentId in row: {student}")
                # Decide if this should be a hard error or just a skipped row
                # For now, we skip but a more robust app might return a 400 if studentId is critical for ALL
                pass # Continue processing other students if studentId is missing for one
        
        batch.commit() 
        return jsonify({"message": f"Successfully uploaded {len(students_to_add)} students!"}), 200

    except Exception as e:
        print(f"ERROR during student CSV upload: {e}")
        return jsonify({"error": "An unexpected server error occurred during student upload. Please check backend logs."}), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    """
    API endpoint to retrieve all student data from Firestore.
    """
    try:
        students_ref = db.collection(f'artifacts/{PROJECT_ID}/public/data/students')
        docs = students_ref.stream()
        students_list = []
        for doc in docs:
            students_list.append(doc.to_dict()) 
        return jsonify(students_list), 200
    except Exception as e:
        print(f"ERROR fetching students: {e}")
        return jsonify({"error": "An internal server error occurred while fetching student data. Please try again."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)



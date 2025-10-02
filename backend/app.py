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
    cred_path = "serviceAccountKey.json"
    if not os.path.exists(cred_path):
        print(f"ERROR: serviceAccountKey.json not found at {cred_path}")
        print("Please ensure your Firebase Admin SDK service account key is in the project's root folder.")
        raise FileNotFoundError("serviceAccountKey.json missing")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"ERROR: Firebase Admin SDK initialization failed: {e}")
    # Do not exit silently in library; propagate
    raise

PROJECT_ID = firebase_admin.get_app().project_id
print(f"Using Firebase Project ID as appId for Firestore paths: {PROJECT_ID}")


@app.route('/')
def hello_world():
    return 'Flask Backend for Attendance System is running!'


@app.route('/api/students/upload', methods=['POST'])
def upload_students():
    """
    Upload student CSV(s). Expected headers: rollNumber,branch,section,academicYear
    Multiple files supported (each appended).
    """
    if 'files' not in request.files:
        return jsonify({"error": "No file part (expected form field name 'files')"}), 400

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({"error": "No selected file"}), 400

    students_to_add = []

    required_headers = ['studentId','rollNumber', 'name', 'branch', 'section', 'academicYear']


    for file in files:
        if file and file.filename.lower().endswith('.csv'):
            try:
                stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
                csv_reader = csv.DictReader(stream)
            except Exception as e:
                return jsonify({"error": f"Failed to read CSV file {file.filename}: {e}"}), 400

            if not csv_reader.fieldnames:
                return jsonify({"error": f"No headers found in CSV {file.filename}"}), 400

            # Accept header variations (case-insensitive)
            fieldnames_lower = [h.strip().lower() for h in csv_reader.fieldnames]
            if not all(req.lower() in fieldnames_lower for req in required_headers):
                return jsonify({"error": f"Missing required headers in CSV {file.filename}. Expected: {', '.join(required_headers)}"}), 400

            for row in csv_reader:
                # Normalize row keys (case-insensitive)
                row_norm = {k.strip().lower(): v for k, v in row.items() if k is not None}
                roll_number = row_norm.get('rollnumber', '').strip()
                branch = row_norm.get('branch', '').strip()
                section = row_norm.get('section', '').strip()
                academic_year = row_norm.get('academicyear', '').strip()

                if roll_number and branch and section and academic_year:
                    # create studentId consistent with frontend's expectations:
                    student_id = f"{branch}-{section}-{academic_year}-{roll_number}".replace(" ", "_").lower()
                    # Use roll number as name placeholder if name not provided
                    name = row_norm.get('name') or f"Student {roll_number}"
                    student = {
                        'studentId': student_id,
                        'rollNumber': roll_number,
                        'name': name,
                        'branch': branch,
                        'section': section,
                        'academicYear': academic_year
                    }
                    students_to_add.append(student)

    if not students_to_add:
        return jsonify({"error": "No valid student data found in provided CSV file(s)."}), 400

    try:
        batch = db.batch()
        students_ref = db.collection(f'artifacts/{PROJECT_ID}/public/data/students')
        for student in students_to_add:
            doc_ref = students_ref.document(student['studentId'])
            batch.set(doc_ref, student)
        batch.commit()
        return jsonify({"message": f"Successfully uploaded {len(students_to_add)} students!"}), 200
    except Exception as e:
        print(f"ERROR during student CSV upload: {e}")
        return jsonify({"error": "An unexpected server error occurred during student upload. Check backend logs."}), 500


@app.route('/api/students', methods=['GET'])
def get_students():
    """
    Return all students stored under artifacts/{PROJECT_ID}/public/data/students
    """
    try:
        students_ref = db.collection(f'artifacts/{PROJECT_ID}/public/data/students')
        docs = students_ref.stream()
        students_list = []
        for doc in docs:
            data = doc.to_dict()
            # Ensure required fields exist
            students_list.append({
                'studentId': data.get('studentId') or doc.id,
                'rollNumber': data.get('rollNumber') or '',
                'name': data.get('name') or '',
                'branch': data.get('branch') or '',
                'section': data.get('section') or '',
                'academicYear': data.get('academicYear') or ''
            })
        return jsonify(students_list), 200
    except Exception as e:
        print(f"ERROR fetching students: {e}")
        return jsonify({"error": "An internal server error occurred while fetching student data."}), 500


if __name__ == '__main__':
    # Keep debug True for easier troubleshooting during development (remove/disable in production)
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))




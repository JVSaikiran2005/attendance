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
    # Propagate so failure is visible during dev/testing
    raise

PROJECT_ID = firebase_admin.get_app().project_id
print(f"Using Firebase Project ID as appId for Firestore paths: {PROJECT_ID}")


@app.route('/')
def hello_world():
    return 'Flask Backend for Attendance System is running!'


@app.route('/api/students/upload', methods=['POST'])
def upload_students():
    """
    Upload student CSV(s). Expected headers (case-insensitive): studentId, rollNumber, name, branch, section, academicYear
    Multiple files supported (each appended).
    IMPORTANT: If the CSV contains a studentId value for a row, that value will BE USED as-is (trimmed).
    If studentId is missing/empty in a row, a fallback id is generated from branch-section-academicYear-rollNumber.
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
            fieldnames_lower = [h.strip().lower() for h in csv_reader.fieldnames if h]
            # Ensure required headers are present (based on your UI instruction the CSV must include studentId)
            if not all(req.lower() in fieldnames_lower for req in required_headers):
                return jsonify({"error": f"Missing required headers in CSV {file.filename}. Expected: {', '.join(required_headers)}"}), 400

            for row in csv_reader:
                # Normalize row keys (case-insensitive)
                row_norm = {}
                for k, v in (row.items() if row else []):
                    if k is None:
                        continue
                    if v is None:
                        v = ''
                    row_norm[k.strip().lower()] = v.strip()

                # Read fields (case-insensitive)
                csv_student_id = row_norm.get('studentid', '') or ''
                roll_number = row_norm.get('rollnumber', '') or ''
                branch = row_norm.get('branch', '') or ''
                section = row_norm.get('section', '') or ''
                academic_year = row_norm.get('academicyear', '') or ''
                name = row_norm.get('name', '') or (f"Student {roll_number}" if roll_number else "")

                # Basic validation
                if not roll_number or not branch or not section or not academic_year:
                    # skip incomplete rows
                    continue

                # Respect provided studentId when present; else compute fallback
                if csv_student_id:
                    # Keep as given (trimmed). IMPORTANT: do not mutate it to a computed form to avoid "changing" IDs.
                    student_id = csv_student_id
                else:
                    # fallback generation (keep previous behavior when studentId not provided)
                    student_id = f"{branch}-{section}-{academic_year}-{roll_number}".replace(" ", "_").lower()

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
            # Overwrite or create document with this studentId. We intentionally use set() (not merge) because
            # the CSV upload is an explicit source-of-truth. If you want to merge fields, change to .set(..., merge=True)
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
            data = doc.to_dict() or {}
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


@app.route('/api/students', methods=['POST'])
def add_student():
    """
    Add a single student (JSON body). Accept fields:
    - studentId (optional; if provided, used as-is after trimming)
    - rollNumber (required)
    - name (optional)
    - branch (required)
    - section (required)
    - academicYear (required)
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    if not data:
        return jsonify({"error": "Empty request body"}), 400

    roll_number = str(data.get('rollNumber') or '').strip()
    branch = str(data.get('branch') or '').strip()
    section = str(data.get('section') or '').strip()
    academic_year = str(data.get('academicYear') or '').strip()
    name = str(data.get('name') or '').strip()
    csv_student_id = str(data.get('studentId') or '').strip()

    if not roll_number or not branch or not section or not academic_year:
        return jsonify({"error": "Missing required fields: rollNumber, branch, section, academicYear"}), 400

    # If studentId provided, use as-is (trimmed). Else compute fallback (consistent with CSV fallback).
    if csv_student_id:
        student_id = csv_student_id
    else:
        student_id = f"{branch}-{section}-{academic_year}-{roll_number}".replace(" ", "_").lower()

    student_doc = {
        'studentId': student_id,
        'rollNumber': roll_number,
        'name': name or f"Student {roll_number}",
        'branch': branch,
        'section': section,
        'academicYear': academic_year
    }

    try:
        students_ref = db.collection(f'artifacts/{PROJECT_ID}/public/data/students')
        doc_ref = students_ref.document(student_id)
        doc_ref.set(student_doc)
        return jsonify({"message": f"Student {student_id} added/updated successfully", "studentId": student_id}), 200
    except Exception as e:
        print(f"ERROR adding student: {e}")
        return jsonify({"error": "An internal server error occurred while adding student."}), 500


@app.route('/api/students/<string:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """
    Delete a student document by studentId.
    """
    if not student_id:
        return jsonify({"error": "No studentId provided"}), 400
    try:
        students_ref = db.collection(f'artifacts/{PROJECT_ID}/public/data/students')
        doc_ref = students_ref.document(student_id)
        # Confirm existence (optional) - attempt delete either way
        doc_ref.delete()
        return jsonify({"message": f"Student {student_id} deleted"}), 200
    except Exception as e:
        print(f"ERROR deleting student {student_id}: {e}")
        return jsonify({"error": "An internal server error occurred while deleting student."}), 500


if __name__ == '__main__':
    # Keep debug True for easier troubleshooting during development (remove/disable in production)
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))





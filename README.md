# 🏫 Online Attendance System

A complete online attendance system featuring separate portals for **Lecturers** and **Students**, built with a Python (Flask) backend and a vanilla JavaScript frontend using Tailwind CSS for styling. Data is securely managed using **Google Firestore**.

The system is designed to handle student data management (via CSV upload or single entry) and allows lecturers to mark, save, and view historical attendance, while students can check their individual records and overall percentage.

## 🚀 Key Features

### Frontend (index.html)
* **Dual Portals:** Separate login flows and interfaces for **Lecturers** and **Students**.
* **Modern UI:** Clean, responsive design built with **Tailwind CSS** and the **Inter** font.
* **Firebase Authentication:** Uses Firebase Auth for lecturer email/password login and student anonymous login.
* **Student View:** Allows students to view their details, overall attendance percentage, and a history of their attendance records.
* **Lecturer View:** Provides tools for:
    * Uploading student lists via **CSV**.
    * Adding or deleting individual student records.
    * Filtering students by **Branch, Section, and Academic Year** to mark daily attendance.
    * Viewing historical attendance records in a tabular format.

### Backend (app.py)
* **Flask API:** A lightweight Python server built with Flask.
* **Firestore Integration:** Uses the **Firebase Admin SDK** to manage data in **Firestore**.
* **Student Management Endpoints:**
    * `POST /api/students/upload`: Handles multi-file CSV uploads for bulk student creation/updates.
    * `POST /api/students`: Adds or updates a single student record.
    * `GET /api/students`: Retrieves the complete list of students.
    * `DELETE /api/students/<student_id>`: Removes a student record.
* **Attendance Storage:** Attendance records are stored in Firestore using the path `artifacts/{PROJECT_ID}/public/data/attendance`.

## 🛠️ Technology Stack

* **Frontend:** HTML5, CSS (Tailwind CSS), Vanilla JavaScript
* **Backend:** Python 3, Flask, `flask-cors`
* **Database/Auth:** Google Firebase / Firestore (via Firebase Admin SDK and Firebase JS SDK)

## 📋 Prerequisites

To run this project, you need:

1.  **Python 3** and `pip`.
2.  A **Firebase Project** set up with Firestore.
3.  **Firebase Authentication** enabled (Email/Password for Lecturers, Anonymous for Students).
4.  **Backend Dependencies:** Install the required Python packages:
    ```bash
    pip install Flask flask-cors firebase-admin
    ```
5.  A **Service Account Key** JSON file from your Firebase project, named **`serviceAccountKey.json`**, placed in the root directory of the backend (`app.py`).

## 🚀 Getting Started

### 1. Backend Setup

1.  **Firebase Configuration:** Ensure your Firestore database is initialized and security rules are set up to allow the necessary reads/writes.
2.  **Service Account Key:** Obtain your `serviceAccountKey.json` from your Firebase project settings and place it in the same directory as `app.py`.
3.  **Run the Flask Server:**
    ```bash
    python app.py
    ```
    python -m venv venv Activate the Virtual Environment:

Windows: .\venv\Scripts\activate macOS/Linux: source venv/bin/activate Install Dependencies:

pip install -r requirements.txt (Ensure requirements.txt contains Flask, Flask-CORS, firebase-admin, pandas, openpyxl, PyPDF2)
pip install flask-cors pip install Flask firebase-admin pandas flask-cors
    The server will run on `http://127.0.0.1:5000` by default.

### 2. Frontend Setup

1.  **Configuration Check:** Open `index.html` and ensure the `firebaseConfig` block in the `<script type="module">` matches your Firebase project settings (e.g., `apiKey`, `authDomain`, `projectId`, etc.).
2.  **Open the App:** Simply open the `index.html` file in your web browser. The frontend assumes the backend is running on `http://127.0.0.1:5000`.

## 🔑 Usage and Login

### Lecturer Login
1.  On the sign-in screen, select **Lecturer**.
2.  Enter the **Email** and **Password** of a lecturer account configured in your Firebase Authentication.
3.  The Lecturer Portal will appear, allowing access to student management and attendance marking tools.

### Student Login
1.  On the sign-in screen, select **Student**.
2.  Enter your **Student ID** or **Roll Number**.
3.  The system performs a local lookup against the fetched student list. If found, it uses Firebase Anonymous Authentication and switches to the Student Portal.

## 📂 File Structure

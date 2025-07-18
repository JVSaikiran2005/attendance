Setup Instructions
Follow these steps to get the project up and running on your local machine.

1. Firebase Project Setup
Create a Firebase Project:

Go to the Firebase Console.
Click "Add project" and follow the on-screen instructions.
Give your project a name (e.g., engineering-results-portal or jvskresults).
Enable Google Analytics if desired (optional).
Once created, go to your project dashboard.
Set up Firestore Database:

In the Firebase Console, navigate to "Build" > "Firestore Database".
Click "Create database".
Choose "Start in production mode" (you will set up rules later).
Select a location for your database (e.g., nam5 for North America, asia-south1 for Mumbai).
Click "Enable".
Configure Firestore Security Rules:

While in "Firestore Database", go to the "Rules" tab.
Replace the default rules with the following. These rules allow public read access (for students) and authenticated write access (for admins).
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow public read access to student results
    // Allow write access only if the user is authenticated (e.g., an admin)
    match /artifacts/{appId}/public/data/studentResults/{document=**} {
      allow read;
      allow write: if request.auth != null;
    }
  }
}
Click "Publish".
Enable Email/Password Authentication:

In the Firebase Console, navigate to "Build" > "Authentication".
Click on the "Sign-in method" tab.
Find "Email/Password" in the list. Click the pencil icon (✏️).
Toggle the switch to "Enable" it.
Click "Save".
Create an Admin User Account:

Still in "Authentication", go to the "Users" tab.
Click the "Add user" button.
Enter an email address (e.g., admin@yourcollege.com) and a strong password. This will be your admin login.
Click "Add user".
Generate Firebase Admin SDK Service Account Key:

In the Firebase Console, go to "Project settings" (gear icon next to "Project overview").
Go to the "Service accounts" tab.
Click "Generate new private key".
Click "Generate key". This will download a JSON file (e.g., your-project-id-firebase-adminsdk-xxxxx-xxxxxxxxxx.json).
Rename this downloaded file to serviceAccountKey.json and move it into your backend/ directory.
KEEP THIS FILE SECURE! Do not share it publicly or commit it to public repositories.
Get Firebase Web App Configuration:

In "Project settings", go to the "Your apps" card.
Click on the Web app icon (</>) if you haven't added a web app yet, or select your existing web app.
Copy the firebaseConfig object. It will look something like this:
const firebaseConfig = {
  apiKey: "AIzaSyC...",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project-id.appspot.com",
  messagingSenderId: "1234567890",
  appId: "1:1234567890:web:abcdef1234567890",
  measurementId: "G-XXXXXXXXXX" // Optional
};
You will paste this into your frontend/index.html in a later step.
2. Backend Setup (Python Flask)
Navigate to the Backend Directory:

cd engineering-results-portal/backend
Create a Python Virtual Environment:

python -m venv venv
Activate the Virtual Environment:

Windows:
.\venv\Scripts\activate
macOS/Linux:
source venv/bin/activate
Install Dependencies:

pip install -r requirements.txt
(Ensure requirements.txt contains Flask, Flask-CORS, firebase-admin, pandas, openpyxl, PyPDF2)

Verify serviceAccountKey.json:

Make sure the serviceAccountKey.json file you downloaded from Firebase is in the backend/ directory.
Run the Flask Backend Server:

python app.py
You should see output indicating the server is running on http://127.0.0.1:5000. Keep this terminal window open and running.

3. Frontend Setup (HTML, CSS, JavaScript)
Navigate to the Frontend Directory:

cd engineering-results-portal/frontend
Open index.html in VS Code:

Open the index.html file in your VS Code editor.
Update Firebase Configuration:

Locate the <script type="module"> block near the end of the <body> tag.
Find the firebaseConfig object.
Replace the placeholder values with the actual firebaseConfig you copied from the Firebase Console (Step 1.7).
const firebaseConfig = {
  apiKey: "YOUR_ACTUAL_API_KEY_HERE",
  authDomain: "YOUR_ACTUAL_AUTH_DOMAIN_HERE",
  projectId: "YOUR_ACTUAL_PROJECT_ID_HERE",
  storageBucket: "YOUR_ACTUAL_STORAGE_BUCKET_HERE",
  messagingSenderId: "YOUR_ACTUAL_MESSAGING_SENDER_ID_HERE",
  appId: "YOUR_ACTUAL_APP_ID_HERE",
  // measurementId: "YOUR_ACTUAL_MEASUREMENT_ID_HERE" // Include if present
};
Save index.html.

Run the Frontend:

If you have the VS Code Live Server extension, right-click index.html in the VS Code Explorer and select "Open with Live Server".
Alternatively, open the index.html file directly in your web browser (e.g., by dragging it into the browser window). The URL will typically be file:///.../index.html or http://127.0.0.1:5500/index.html if using Live Server.
Note: Using Live Server (http://127.0.0.1:5500) is recommended as it correctly simulates a web server environment, which is important for network requests to your Flask backend.


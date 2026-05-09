# Real-Time Face Detection Video Streaming System

A containerized full-stack application that captures video from your webcam, detects faces using MediaPipe, stores detection data in a database, and streams the annotated video back to your browser in real-time.

---

## ⚡ Quick Start for Everyone (5 Minutes)

Follow these steps **exactly as written** — no technical knowledge required.

### Step 1: Download and Install Docker
1. Go to https://www.docker.com/products/docker-desktop
2. Click "Download" and run the installer
3. Open Docker Desktop from your Start menu
4. Wait for it to show "Docker Desktop is running" (takes ~1 minute)

### Step 2: Get the Project Files
1. Look at your file explorer and find the folder: `Real-Time Face Detection(mega Ai)`
2. This is your project folder — keep it open

### Step 3: Copy the Configuration File
1. Open the file: `→ .env.example`
2. Press `Ctrl+C` to copy it
3. In the same folder, paste it with `Ctrl+V`
4. Rename the copy from `.env.example (copy)` to `.env`
   - Right-click → Rename
   - Delete everything except `.env`

### Step 4: Start the Application
1. Right-click inside the project folder
2. Click "Open PowerShell window here" (or Command Prompt)
3. Copy and paste this command:
   ```
   docker compose up --build
   ```
4. Press Enter and wait ~30 seconds
5. You should see green checkmarks and "Uvicorn running"

### Step 5: Open Your Browser
1. Open Chrome, Edge, or Firefox
2. Type in the address bar: `http://localhost:3000`
3. Press Enter
4. You should see the app with a **"Start Camera"** button

### Step 6: Test the Face Detection
1. Click the green **"Start Camera"** button
2. Allow camera access when the browser asks
3. Point your camera at your face
4. You should see:
   - Your live face in the video panel with a **green box** around it
   - A table below showing detections with coordinates and confidence scores

---

## 📂 Important Files to Know

| File | What It Does |
|------|-------------|
| `.env.example` → Copy to `.env` | Configuration file (stores passwords safely) |
| `docker-compose.yml` | Tells Docker how to run the app |
| `docs/architecture.png` | Visual diagram showing how everything works |
| `backend/` folder | The AI and video processing code |
| `frontend/` folder | The website you see in the browser |
| `SUBMISSION_NOTES.md` | Summary for assignment reviewers |
| `ASSIGNMENT_VERIFICATION.md` | Checklist proving all requirements are met |

---

## 🛑 Troubleshooting

### Problem: Docker is not starting
- **Solution:** Restart your computer and try again

### Problem: The browser shows "Cannot connect"
- **Solution:** Wait another 30 seconds — Docker is still starting
- Check PowerShell window for errors

### Problem: No camera access popup
- **Solution:** Your browser blocked it. Click the camera icon in the address bar and click "Allow"

### Problem: Face not detected
- **Solution:** Make sure:
  - Your face is in good lighting
  - Your camera is facing you
  - The window is large enough

---

## 🏗 How It Works (Non-Technical Explanation)

1. **Your Webcam** captures your face
2. **Browser** sends the image to the backend server
3. **Backend** uses AI to detect your face and draws a green box around it
4. **Backend** saves information about where your face is (coordinates, confidence)
5. **Backend** sends the annotated image back to the browser
6. **Your Screen** displays the live video with the green box
7. **The Table** below shows all the faces detected with their exact positions

---

## 🎯 What You're Testing

✅ Real-time face detection with AI  
✅ Video streaming from server to browser  
✅ Database storage of detection data  
✅ Live ROI (Region of Interest) visualization  
✅ No OpenCV library used — uses MediaPipe instead  

---

## 📋 Tech Stack

- **Backend:** FastAPI (the server), MediaPipe (face AI), Pillow (drawing boxes), PostgreSQL (database)
- **Frontend:** React.js (interactive website), Nginx (web server)
- **Infrastructure:** Docker (containerization)

---

## 🔐 Security

- All passwords are stored in the `.env` file (never in the code)
- Database access uses secure queries that prevent hacking
- Your webcam feed only goes to your local computer
- No data is sent to the internet

---

## ✅ Tests

The project includes automated tests that verify:
- Face detection works correctly
- Bounding boxes are drawn properly
- ROI data is saved to the database
- No OpenCV is used anywhere

To run tests after setup:
```
python -m pytest backend/tests/
```

---

## 📖 For Reviewers / More Details

- See **`SUBMISSION_NOTES.md`** for the 5-minute reviewer path
- See **`ASSIGNMENT_VERIFICATION.md`** for detailed requirement checklist
- See **`DEPLOYMENT_GUIDE.md`** for advanced setup options
- See **`docs/architecture.png`** for system diagram

---

## 🤖 AI Collaboration

This project was developed with AI assistance. The AI helped with:
- Writing the server code (FastAPI)
- Building the website (React)
- Setting up the database
- Creating the documentation

All code was tested locally against a real webcam to ensure it works correctly.

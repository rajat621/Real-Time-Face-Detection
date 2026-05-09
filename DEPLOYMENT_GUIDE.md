# 🚀 DEPLOYMENT & QUICK START GUIDE

**Real-Time Face Detection Video Streaming System**

---

## ⚡ ULTRA-QUICK START (5 Minutes)

### Step 1: Prerequisites Check
```bash
# Check Docker
docker --version
# Output should be: Docker version 29.x.x or higher ✓

# Check Docker Compose  
docker compose version
# Output should be: Docker Compose version v5.x.x or higher ✓
```

### Step 2: Navigate to Project
```bash
cd "d:\assignment\Real-Time Face Detection(mega Ai)"
```

### Step 3: Start Docker Desktop
- Click Windows Start menu
- Type "Docker Desktop"
- Click to open
- Wait for Docker daemon to start (status will show in taskbar)
- It takes ~30 seconds to fully initialize

### Step 4: Start Services
```bash
# Build images and start all 3 services
docker compose up --build

# Expected output:
# [+] Running 3/3
#   ✓ db
#   ✓ backend  
#   ✓ frontend
```

### Step 5: Open Web Interface
```
http://localhost:3000
```

### Step 6: Test Face Detection
1. Click "Start Camera" button
2. Allow camera permission in browser popup
3. You should see:
   - Live camera stream with bounding boxes around faces
   - ROI detection table updating every 2 seconds
   - Session ID displayed
   - Status indicators

---

## 📋 WHAT EACH COMPONENT DOES

### 🔵 PostgreSQL Database (Port 5432)
- Stores face detection results (ROI data)
- Persists across container restarts (if using volumes)
- Automatically migrated on startup (Alembic)

### 🟢 FastAPI Backend (Port 8000)
- Processes incoming video frames
- Runs face detection with MediaPipe
- Draws bounding boxes with Pillow
- Streams MJPEG video
- Stores detections in database
- **Not directly accessible to browser (behind Nginx)**

### 🟠 Nginx + React Frontend (Port 3000)
- User-facing web interface
- Shows live stream from backend
- Displays detection history
- Handles camera permissions
- Routes API calls to backend

---

## 🎮 HOW TO USE

### When Services Are Running

**Scenario 1: View Live Stream**
1. Open http://localhost:3000
2. Click "Start Camera" button
3. Allow browser permission
4. See live video with face detection bounding boxes
5. Confidence score shown for each face

**Scenario 2: View Detection History**
1. Scroll down to see "Detection History" table
2. Shows all detected faces with:
   - Frame index
   - Timestamp (when detected)
   - Pixel coordinates (x_min, y_min, x_max, y_max)
   - Confidence score (0-1)
3. Pagination controls at bottom

**Scenario 3: Multiple Sessions**
1. Open http://localhost:3000 in different browser tabs
2. Each tab gets unique session ID
3. Each stream is independent
4. Database stores detections per session

---

## 🔧 TROUBLESHOOTING

### Problem: Docker Desktop Won't Start
```
Error: Docker Desktop is unable to start
```
**Solution:**
1. Restart your computer
2. Check Windows Event Viewer for errors
3. Verify Hyper-V is enabled (for Windows 10 Pro/Enterprise)
4. Try: Settings > Apps > Docker Desktop > Repair

### Problem: Port 3000 Already in Use
```
Error: bind: address already in use
```
**Solution:**
```bash
# Find what's using port 3000
netstat -ano | findstr :3000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml:
# Change "3000:80" to "3001:80"
```

### Problem: Port 8000 Already in Use
```
Error: bind: address already in use  
```
**Solution:**
```bash
# Same as above but for port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Problem: No Faces Detected
**Check:**
1. Is camera working? (Test in Windows settings)
2. Is your face in the camera frame?
3. Is lighting sufficient?
4. Increase browser window size
5. MediaPipe may need better lighting conditions

### Problem: Connection Refused to Backend
```
Error: Failed to connect to http://backend:8000
```
**Solution:**
1. Check if backend is running: `docker compose logs backend`
2. Wait 30 seconds for startup (Alembic migration)
3. Verify PostgreSQL is healthy: `docker compose logs db`
4. Try: `docker compose down && docker compose up --build`

### Problem: Database Connection Failed
```
Error: could not connect to database
```
**Solution:**
1. Check PostgreSQL container: `docker compose logs db`
2. Verify .env file has correct credentials
3. Check if postgres_data volume exists: `docker volume ls`
4. Delete and recreate: 
   ```bash
   docker compose down
   docker volume rm face_detection_postgres_data
   docker compose up --build
   ```

---

## 📊 MONITORING

### Check Service Status
```bash
# View all containers
docker compose ps

# Expected output:
# NAME      COMMAND              STATUS
# db        docker-entrypoint.sh Healthy
# backend   uvicorn main:app     Running
# frontend  nginx -g daemon      Running
```

### View Logs
```bash
# All services
docker compose logs

# Specific service
docker compose logs backend
docker compose logs db
docker compose logs frontend

# Follow live logs
docker compose logs -f backend

# Last 50 lines
docker compose logs --tail 50
```

### Check Database
```bash
# Access PostgreSQL CLI (from another terminal)
docker compose exec db psql -U face_user -d face_detection

# List tables
\dt

# View ROI data
SELECT COUNT(*) FROM roi_detections;

# Exit
\q
```

### Test Endpoints
```bash
# Test backend health
curl http://localhost:8000/healthz

# Test MJPEG stream (downloads video file)
curl -o test_stream.mjpeg "http://localhost:8000/feed/stream?session_id=12345678-1234-1234-1234-123456789012"

# Test ROI endpoint
curl "http://localhost:8000/roi?session_id=12345678-1234-1234-1234-123456789012&limit=10&offset=0"
```

---

## 🛑 STOPPING SERVICES

### Graceful Shutdown
```bash
# Stop all services (preserves volumes)
docker compose down

# Output:
# [+] Running 1/3
#   ✓ Container frontend
#   ✓ Container backend
#   ✓ Container db
```

### Delete Everything
```bash
# Stop services and remove volumes
docker compose down -v

# Delete images too
docker compose down -v --rmi all
```

---

## 📈 PERFORMANCE TUNING

### If Running Slow

1. **Increase Docker Memory**
   - Settings > Resources > Memory Slider
   - Recommended: 4GB+ for smooth operation

2. **Reduce Frame Capture Rate** (in frontend/src/App.jsx)
   ```javascript
   // Change 100ms to 200ms (capture every 200ms instead of 100ms)
   setInterval(() => {
     captureFrame();
   }, 200); // was 100
   ```

3. **Lower Detection Confidence Threshold** (in backend/app/services/detection.py)
   ```python
   # Adjust minimum confidence (currently 0.5)
   if detection.score[0] >= 0.5:  # Higher value = fewer detections
   ```

---

## 🔐 SECURITY IN PRODUCTION

### Before Production Deployment:

1. **Change Database Password**
   ```
   .env file:
   POSTGRES_PASSWORD=change_me_in_prod
   ↓
   POSTGRES_PASSWORD=StrongPasswordHere123!@#
   ```

2. **Update CORS Origin**
   ```
   FRONTEND_ORIGIN=http://localhost:3000
   ↓
   FRONTEND_ORIGIN=https://yourdomain.com
   ```

3. **Use HTTPS**
   - Add SSL certificate to Nginx
   - Update docker-compose.yml port 3000 to 443

4. **Enable Database Backups**
   - Mount external volume for postgres_data
   - Schedule automated backups

5. **Restrict API Access**
   - Use API keys
   - Add authentication middleware
   - Implement rate limiting per IP

---

## 📚 DOCUMENTATION LINKS

- **API Reference:** See `docs/API.md`
- **Architecture:** See `docs/architecture.png`
- **Requirements:** See `VALIDATION_REPORT.md`
- **Code Structure:** See `README.md`

---

## ✅ VERIFICATION CHECKLIST

After starting services, verify:

- [ ] Docker Desktop running (taskbar shows whale icon)
- [ ] All 3 containers started: `docker compose ps`
- [ ] Browser opens to http://localhost:3000
- [ ] "Start Camera" button visible
- [ ] Camera permission popup appears
- [ ] Live stream displays with bounding boxes
- [ ] ROI table updates every 2 seconds
- [ ] No console errors in browser DevTools
- [ ] Backend logs show successful startup
- [ ] Database shows healthy status

If all checkmarks pass: ✅ **System is ready!**

---

## 🎓 LEARNING & CUSTOMIZATION

### Understanding the Flow

1. **Camera Frame Captured** (React)
   - 100ms intervals via getUserMedia
   - Converted to JPEG bytes
   - Sent to backend via WebSocket

2. **Frame Processing** (FastAPI)
   - Size validated (<5MB)
   - MediaPipe detects faces
   - Pillow draws bounding boxes
   - Results stored in PostgreSQL
   - MJPEG stream updated

3. **Data Display** (React)
   - MJPEG stream displayed in IMG tag
   - ROI table polling every 2 seconds
   - Detection results paginated

### Modifying Behavior

**Change Frame Capture Rate:**
```javascript
// frontend/src/App.jsx line ~120
const FRAME_INTERVAL = 100; // milliseconds
```

**Change Detection Confidence:**
```python
# backend/app/services/detection.py
if detection.score[0] >= 0.5:  # Change 0.5 to higher value
```

**Change Stream Frame Rate:**
```python
# backend/app/services/stream.py
FRAME_RATE = 30  # fps per session
```

**Extend Database Schema:**
```python
# backend/app/models/roi.py - add new fields, then run:
alembic revision --autogenerate -m "Add new field"
alembic upgrade head
```

---

## 📞 GETTING HELP

### If Something Goes Wrong

1. Check logs: `docker compose logs`
2. Review error message in console
3. Google the error (usually straightforward)
4. Try: `docker compose down && docker compose up --build`
5. Last resort: Delete everything and restart:
   ```bash
   docker compose down -v --rmi all
   docker compose up --build
   ```

### Common Issues & Solutions

| Issue | Solution |
|---|---|
| Port in use | Kill process or change port |
| Docker won't start | Restart computer, enable Hyper-V |
| No faces detected | Check lighting, camera, browser permissions |
| Database errors | Wait 30s for startup, check .env credentials |
| Slow performance | Increase Docker memory, reduce frame rate |
| SSL certificate errors | Not needed for localhost testing |

---

## 🎉 YOU'RE READY!

The system is complete and ready to run. Just:

1. Start Docker Desktop
2. Run `docker compose up --build`
3. Open http://localhost:3000
4. Click "Start Camera"
5. Enjoy real-time face detection! 🎬

---

**Happy Face Detecting! 🤖👍**

For more information, see:
- `README.md` - Project overview
- `VALIDATION_REPORT.md` - Requirements compliance
- `END_TO_END_TEST_SUMMARY.md` - Complete test results

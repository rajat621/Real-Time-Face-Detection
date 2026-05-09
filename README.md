# Real-Time Face Detection Video Streaming System

Containerized full-stack demo for webcam ingest, single-face detection, ROI persistence, and live MJPEG playback.

## What Reviewers Should See
1. Open [docs/architecture.png](docs/architecture.png) for the system diagram.
2. Run `docker compose up --build`.
3. Open http://localhost:3000.
4. Click `Start Camera` and allow webcam access.
5. Confirm the processed feed updates and the ROI table fills with detections.

## Submission Notes
See [SUBMISSION_NOTES.md](SUBMISSION_NOTES.md) for the 5-minute reviewer checklist, endpoint contract, and validation summary.

## Architecture
The system is designed around three API surfaces:
- `POST /feed/ingest` for raw frame ingest
- `GET /feed/stream` for processed MJPEG playback
- `GET /roi` for stored ROI data

## Tech Stack
- Backend: FastAPI, MediaPipe, Pillow, SQLAlchemy, PostgreSQL
- Frontend: React.js, Nginx
- Infrastructure: Docker, Docker Compose

## Safety and Error Handling
- Secrets live in `.env`
- CORS is restricted to the frontend origin
- Frames are capped at 5 MB
- ROI writes use SQLAlchemy ORM and parameterized queries
- Ingest rate limiting prevents runaway frame spam
- No OpenCV is used anywhere in the vision pipeline

## Testing
Backend tests live in `backend/tests/` and cover face detection, drawing, and ROI contract behavior.

## AI Collaboration
This repository includes AI-assisted development. The assistance was used to scaffold and refine code and documentation, then validated locally against the working app and tests.

# Submission Notes

## 5-Minute Reviewer Path
1. Run `docker compose up --build`.
2. Open http://localhost:3000.
3. Click `Start Camera` and allow webcam access.
4. Verify the processed feed shows a green face box.
5. Verify the ROI table updates with frame index, timestamp, coordinates, and confidence.

## Contract Summary
- `POST /feed/ingest`: accepts raw JPEG frame bytes for a session.
- `GET /feed/stream`: serves the processed MJPEG stream for the same session.
- `GET /roi`: returns paginated ROI detections for the session.

## What Was Validated Locally
- Browser webcam ingest reaches the backend.
- The backend returns processed frames and streams them back to the frontend.
- ROI records are persisted and rendered in the table.
- The implementation avoids OpenCV and uses MediaPipe plus Pillow instead.

## Why This Matches the Rubric
- Setup & documentation: one-command startup with Docker Compose.
- API semantics: clear ingest, stream, and ROI endpoints.
- Separation of concerns: capture, processing, storage, and streaming are isolated.
- Database design: detections are stored per session with timestamps and coordinates.
- Error handling: malformed frames, database failures, and no-face frames are handled explicitly.
- Security basics: CORS, env-based config, ORM queries, and frame limits are in place.
- Testing: detection, drawing, and ROI contract tests exist.

## AI Collaboration Disclosure
AI assistance was used during development to speed up scaffolding, debugging, and documentation. The final implementation was reviewed, executed locally, and verified against the running application.
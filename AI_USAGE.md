# AI Collaboration Log

## Tools Used
- GitHub Copilot (agent mode) — primary code generation
- Claude (Anthropic) — prompt engineering and gap analysis

## What AI Generated
- Backend service files (detection.py, drawing.py, processing.py)
- FastAPI routers (feed.py, roi.py)
- React frontend components
- Docker Compose and Nginx configuration
- Alembic migration
- Test files

## What I Verified
- System runs end-to-end with real webcam input (screenshot evidence)
- No OpenCV imports confirmed in production code
- API contracts match specification
- Face bounding box visible in live stream
- ROI table populates in real time

## How AI Was Directed
A detailed specification prompt was written covering every requirement,
constraint, file structure, and error-handling rule before any code
was generated. Output was reviewed against the assignment rubric and
tested locally with Docker.
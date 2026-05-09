"""
End-to-End Test Suite for Real-Time Face Detection System
Tests all requirements and validates the complete workflow
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, ImageDraw

# Configuration
API_BASE_URL = "http://localhost:8000"
SESSION_ID = str(uuid.uuid4())
POSTGRES_URL = "postgresql://face_user:change_me_in_prod@localhost:5432/face_detection"


def create_synthetic_face_frame(width: int = 640, height: int = 480) -> bytes:
    """Create a test JPEG frame with a synthetic face-like pattern."""
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    # Draw a simple face-like pattern (circle + eyes)
    center_x, center_y = width // 2, height // 2
    face_radius = 80

    # Face circle
    draw.ellipse(
        [center_x - face_radius, center_y - face_radius, center_x + face_radius, center_y + face_radius],
        outline="black",
        width=3,
    )

    # Eyes
    eye_size = 10
    draw.ellipse([center_x - 30 - eye_size, center_y - 20 - eye_size, center_x - 30 + eye_size, center_y - 20 + eye_size], fill="black")
    draw.ellipse([center_x + 30 - eye_size, center_y - 20 - eye_size, center_x + 30 + eye_size, center_y - 20 + eye_size], fill="black")

    # Nose
    draw.ellipse([center_x - 5, center_y - 5, center_x + 5, center_y + 5], fill="black")

    # Convert to JPEG bytes
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


async def test_healthz_endpoint():
    """Test that the backend is healthy."""
    print("\n[TEST 1] Testing /healthz endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/healthz", timeout=5.0)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert data.get("status") == "ok"
            print("✓ Backend is healthy")
            return True
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False


async def test_http_ingest_endpoint():
    """Test HTTP POST ingest endpoint."""
    print("\n[TEST 2] Testing POST /feed/ingest (HTTP)...")
    frame_bytes = create_synthetic_face_frame()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/feed/ingest",
                params={"session_id": SESSION_ID, "frame_index": 1},
                content=frame_bytes,
            )

            assert response.status_code in [200, 204], f"Expected 200 or 204, got {response.status_code}"
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Frame ingested: {data.get('status')}")
            else:
                print("✓ Frame ingested (204 - no face detected, as expected for synthetic frame)")
            return True
        except Exception as e:
            print(f"✗ HTTP ingest failed: {e}")
            return False


async def test_websocket_ingest_endpoint():
    """Test WebSocket ingest endpoint."""
    print("\n[TEST 3] Testing WebSocket /feed/ingest...")
    frame_bytes = create_synthetic_face_frame()

    try:
        async with httpx.AsyncClient() as client:
            ws_url = f"ws://localhost:8000/feed/ingest?session_id={SESSION_ID}"

            try:
                async with client.websocket_connect(ws_url) as websocket:
                    # Send a frame
                    await websocket.send_bytes(frame_bytes)

                    # Receive response
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                    data = json.loads(message)

                    assert "status" in data, "Response missing 'status' field"
                    print(f"✓ WebSocket ingest working: {data.get('status')}")
                    return True
            except asyncio.TimeoutError:
                print("✗ WebSocket timeout waiting for response")
                return False
    except Exception as e:
        print(f"✗ WebSocket ingest failed: {e}")
        return False


async def test_roi_rest_endpoint():
    """Test GET /roi endpoint."""
    print("\n[TEST 4] Testing GET /roi (REST endpoint)...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/roi",
                params={"session_id": SESSION_ID, "limit": 50, "offset": 0},
                timeout=5.0,
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()

            # Validate response structure
            assert "session_id" in data
            assert "limit" in data
            assert "offset" in data
            assert "total" in data
            assert "items" in data
            assert isinstance(data["items"], list)

            print(f"✓ ROI endpoint working: {data['total']} detections found")
            if data["items"]:
                item = data["items"][0]
                print(f"  - Sample: x_min={item['x_min']}, y_min={item['y_min']}, x_max={item['x_max']}, y_max={item['y_max']}")
            return True
        except Exception as e:
            print(f"✗ ROI endpoint failed: {e}")
            return False


async def test_mjpeg_stream_endpoint():
    """Test GET /feed/stream MJPEG endpoint."""
    print("\n[TEST 5] Testing GET /feed/stream (MJPEG)...")
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "GET",
                f"{API_BASE_URL}/feed/stream",
                params={"session_id": SESSION_ID},
                timeout=10.0,
            ) as response:
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                assert "multipart/x-mixed-replace" in response.headers.get("content-type", "")

                # Read first chunk
                chunks = []
                async for data in response.aiter_bytes(chunk_size=4096):
                    chunks.append(data)
                    if len(chunks) > 1:
                        break  # Just get a couple chunks to verify streaming works

                assert chunks, "No data received from stream"
                total_bytes = sum(len(c) for c in chunks)
                print(f"✓ MJPEG stream working: received {total_bytes} bytes in {len(chunks)} chunks")
                return True
        except Exception as e:
            print(f"✗ MJPEG stream failed: {e}")
            return False


async def test_database_schema():
    """Verify database schema with SQLAlchemy."""
    print("\n[TEST 6] Testing database schema and queries...")
    try:
        from sqlalchemy import inspect, text
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(POSTGRES_URL, echo=False)

        async with engine.connect() as conn:
            # Check if roi_detections table exists
            inspector = inspect(conn)
            tables = await conn.run_sync(inspector.get_table_names)

            if "roi_detections" not in tables:
                print("✗ roi_detections table not found")
                await engine.dispose()
                return False

            # Get table info
            columns = await conn.run_sync(lambda: inspector.get_columns("roi_detections"))
            column_names = [c["name"] for c in columns]

            expected_columns = ["id", "session_id", "frame_index", "timestamp", "x_min", "y_min", "x_max", "y_max", "confidence"]
            for col in expected_columns:
                if col not in column_names:
                    print(f"✗ Missing column: {col}")
                    await engine.dispose()
                    return False

            # Try a simple query
            result = await conn.execute(text("SELECT COUNT(*) FROM roi_detections"))
            count = result.scalar()
            print(f"✓ Database schema valid: {count} ROI records in database")

        await engine.dispose()
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


async def test_no_opencv_imports():
    """Verify no OpenCV imports in the codebase."""
    print("\n[TEST 7] Verifying NO OpenCV imports (requirement)...")
    backend_path = Path(__file__).parent / "backend"
    violations = []

    for py_file in backend_path.rglob("*.py"):
        if "test_" in py_file.name or ".venv" in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            if "import cv2" in content or "from cv2" in content:
                violations.append(str(py_file))
        except Exception:
            pass

    if violations:
        print(f"✗ Found OpenCV imports in: {violations}")
        return False
    else:
        print("✓ No OpenCV imports found in codebase")
        return True


async def test_pillow_drawing_verification():
    """Verify that drawing uses Pillow, not OpenCV."""
    print("\n[TEST 8] Verifying Pillow-based drawing (no OpenCV)...")
    drawing_file = Path(__file__).parent / "backend" / "app" / "services" / "drawing.py"

    try:
        content = drawing_file.read_text(encoding="utf-8")

        if "from PIL import" in content or "import PIL" in content:
            print("✓ Drawing service uses Pillow (PIL)")
            return True
        else:
            print("✗ Drawing service does not explicitly import Pillow")
            return False
    except Exception as e:
        print(f"✗ Could not verify drawing implementation: {e}")
        return False


async def test_mediapipe_detection():
    """Verify MediaPipe is used for face detection."""
    print("\n[TEST 9] Verifying MediaPipe-based detection...")
    detection_file = Path(__file__).parent / "backend" / "app" / "services" / "detection.py"

    try:
        content = detection_file.read_text(encoding="utf-8")

        if "mediapipe" in content:
            print("✓ Face detection uses MediaPipe")
            return True
        else:
            print("✗ MediaPipe not found in detection module")
            return False
    except Exception as e:
        print(f"✗ Could not verify detection implementation: {e}")
        return False


async def test_docker_compose_structure():
    """Verify Docker Compose file structure."""
    print("\n[TEST 10] Verifying Docker Compose structure...")
    docker_compose_file = Path(__file__).parent / "docker-compose.yml"

    try:
        import yaml

        with open(docker_compose_file) as f:
            compose_data = yaml.safe_load(f)

        required_services = ["db", "backend", "frontend"]
        services = compose_data.get("services", {})

        for service in required_services:
            if service not in services:
                print(f"✗ Missing service: {service}")
                return False

        # Verify volumes for postgres
        if "volumes" not in compose_data or "postgres_data" not in compose_data.get("volumes", {}):
            print("✗ Missing postgres_data volume")
            return False

        print(f"✓ Docker Compose valid: {len(services)} services defined")
        return True
    except ImportError:
        print("⚠ PyYAML not installed, skipping YAML validation")
        return True
    except Exception as e:
        print(f"✗ Docker Compose verification failed: {e}")
        return False


async def test_error_handling():
    """Test error handling for edge cases."""
    print("\n[TEST 11] Testing error handling...")
    results = []

    # Test: Frame too large (>5MB)
    async with httpx.AsyncClient() as client:
        try:
            large_frame = b"x" * (6 * 1024 * 1024)
            response = await client.post(
                f"{API_BASE_URL}/feed/ingest",
                params={"session_id": SESSION_ID},
                content=large_frame,
                timeout=5.0,
            )
            if response.status_code == 413:
                print("✓ Large frame rejected correctly (413)")
                results.append(True)
            else:
                print(f"✗ Large frame not rejected: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"✗ Large frame test error: {e}")
            results.append(False)

    # Test: Malformed JSON on ROI endpoint
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/roi",
                params={"session_id": "not-a-uuid"},
                timeout=5.0,
            )
            if response.status_code == 422:
                print("✓ Invalid session_id rejected correctly (422)")
                results.append(True)
            else:
                print(f"✗ Invalid session_id not rejected: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"✗ Invalid session_id test error: {e}")
            results.append(False)

    return all(results)


async def run_all_tests():
    """Run all end-to-end tests."""
    print("=" * 80)
    print("REAL-TIME FACE DETECTION SYSTEM - END-TO-END TEST SUITE")
    print("=" * 80)
    print(f"Session ID: {SESSION_ID}")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Database: {POSTGRES_URL}")
    print("=" * 80)

    # Allow services to stabilize
    print("\nWaiting for services to be ready...")
    for attempt in range(30):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/healthz", timeout=2.0)
                if response.status_code == 200:
                    print("✓ Services are ready\n")
                    break
        except Exception:
            pass

        if attempt < 29:
            await asyncio.sleep(1)
            print(".", end="", flush=True)
        else:
            print("\n✗ Services did not become ready in time")
            return False

    # Run all tests
    tests = [
        ("API Health", test_healthz_endpoint),
        ("HTTP Ingest", test_http_ingest_endpoint),
        ("WebSocket Ingest", test_websocket_ingest_endpoint),
        ("ROI REST Endpoint", test_roi_rest_endpoint),
        ("MJPEG Stream", test_mjpeg_stream_endpoint),
        ("Database Schema", test_database_schema),
        ("No OpenCV", test_no_opencv_imports),
        ("Pillow Drawing", test_pillow_drawing_verification),
        ("MediaPipe Detection", test_mediapipe_detection),
        ("Docker Compose", test_docker_compose_structure),
        ("Error Handling", test_error_handling),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results[test_name] = False

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 80)
    print(f"Results: {passed}/{total} tests passed ({100 * passed / total:.1f}%)")
    print("=" * 80)

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        exit(1)

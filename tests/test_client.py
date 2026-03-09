"""Tests for the IAES Python SDK Client (v0.2.0).

These tests use a mock HTTP server to verify client behavior
without any external dependencies.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from unittest import TestCase, main

from iaes import Client, IaesClientError, AssetMeasurement, AssetHealth, WorkOrderIntent


class MockHandler(BaseHTTPRequestHandler):
    """Simple mock IAES ingest endpoint."""

    # Class-level storage for assertions
    last_request_body = None
    last_request_headers = {}
    response_code = 201
    response_body = {"accepted": 1, "rejected": 0, "results": []}

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        MockHandler.last_request_body = json.loads(body.decode("utf-8"))
        MockHandler.last_request_headers = dict(self.headers)

        self.send_response(MockHandler.response_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(MockHandler.response_body).encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Suppress server logs


def get_free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class TestClient(TestCase):
    """Test suite for iaes.Client."""

    @classmethod
    def setUpClass(cls):
        cls.port = get_free_port()
        cls.server = HTTPServer(("127.0.0.1", cls.port), MockHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        MockHandler.response_code = 201
        MockHandler.response_body = {
            "accepted": 1,
            "rejected": 0,
            "results": [{"event_id": "test-1", "status": "stored", "routed_to": "measurements"}],
        }
        MockHandler.last_request_body = None
        MockHandler.last_request_headers = {}

    # --- Constructor ---

    def test_trailing_slash_stripped(self):
        client = Client(f"{self.base_url}///", api_key="test-key")
        self.assertEqual(client.base_url, self.base_url)

    def test_custom_ingest_path(self):
        client = Client(self.base_url, ingest_path="/custom/ingest")
        self.assertEqual(client._endpoint, f"{self.base_url}/custom/ingest")

    # --- Publish single event ---

    def test_publish_model_instance(self):
        client = Client(self.base_url, api_key="wk_test123")
        event = AssetMeasurement(
            asset_id="MOTOR-001",
            measurement_type="vibration_velocity",
            value=4.2,
            unit="mm/s",
            source="test",
        )

        result = client.publish(event)

        self.assertEqual(result["accepted"], 1)
        self.assertIsNotNone(MockHandler.last_request_body)
        body = MockHandler.last_request_body
        self.assertEqual(body["event_type"], "asset.measurement")
        self.assertEqual(body["asset"]["asset_id"], "MOTOR-001")
        self.assertEqual(body["data"]["value"], 4.2)

    def test_publish_raw_dict(self):
        client = Client(self.base_url, api_key="wk_test123")
        envelope = {
            "event_type": "asset.measurement",
            "event_id": "raw-1",
            "asset": {"asset_id": "PUMP-001"},
            "data": {"value": 99},
        }

        result = client.publish(envelope)
        self.assertEqual(result["accepted"], 1)
        self.assertEqual(MockHandler.last_request_body["event_id"], "raw-1")

    def test_api_key_sent_as_header(self):
        client = Client(self.base_url, api_key="wk_secret_key")
        event = AssetMeasurement(
            asset_id="M-1", measurement_type="temperature", value=72, unit="°C",
        )
        client.publish(event)

        self.assertEqual(MockHandler.last_request_headers.get("X-Api-Key"), "wk_secret_key")

    def test_user_agent_header(self):
        client = Client(self.base_url)
        event = AssetMeasurement(
            asset_id="M-1", measurement_type="temperature", value=72, unit="°C",
        )
        client.publish(event)

        ua = MockHandler.last_request_headers.get("User-Agent", "")
        self.assertIn("iaes-python-sdk", ua)

    def test_custom_headers(self):
        client = Client(self.base_url, headers={"X-Custom": "value123"})
        event = AssetMeasurement(
            asset_id="M-1", measurement_type="temperature", value=72, unit="°C",
        )
        client.publish(event)

        self.assertEqual(MockHandler.last_request_headers.get("X-Custom"), "value123")

    # --- Batch publish ---

    def test_publish_batch(self):
        MockHandler.response_body = {
            "accepted": 3,
            "rejected": 0,
            "results": [
                {"event_id": "b1", "status": "stored"},
                {"event_id": "b2", "status": "stored"},
                {"event_id": "b3", "status": "stored"},
            ],
        }
        client = Client(self.base_url, api_key="wk_batch")
        events = [
            AssetMeasurement(asset_id="M-1", measurement_type="temperature", value=i, unit="°C")
            for i in range(3)
        ]

        result = client.publish_batch(events)

        self.assertEqual(result["accepted"], 3)
        self.assertIsInstance(MockHandler.last_request_body, list)
        self.assertEqual(len(MockHandler.last_request_body), 3)

    def test_publish_batch_mixed_types(self):
        MockHandler.response_body = {"accepted": 2, "rejected": 0, "results": []}
        client = Client(self.base_url)
        events = [
            AssetMeasurement(asset_id="M-1", measurement_type="temperature", value=50, unit="°C"),
            AssetHealth(asset_id="M-1", health_index=0.85, source="test"),
        ]

        result = client.publish_batch(events)
        self.assertEqual(result["accepted"], 2)
        body = MockHandler.last_request_body
        self.assertEqual(body[0]["event_type"], "asset.measurement")
        self.assertEqual(body[1]["event_type"], "asset.health")

    # --- Error handling ---

    def test_http_error_raises(self):
        MockHandler.response_code = 401
        MockHandler.response_body = {"detail": "Invalid API key"}
        client = Client(self.base_url, api_key="bad-key")
        event = AssetMeasurement(
            asset_id="M-1", measurement_type="temperature", value=50, unit="°C",
        )

        with self.assertRaises(IaesClientError) as ctx:
            client.publish(event)

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("401", str(ctx.exception))

    def test_http_422_raises(self):
        MockHandler.response_code = 422
        MockHandler.response_body = {"detail": "Missing event_type"}
        client = Client(self.base_url)
        event = {"bad": "payload"}

        with self.assertRaises(IaesClientError) as ctx:
            client.publish(event)

        self.assertEqual(ctx.exception.status_code, 422)

    def test_connection_refused_raises(self):
        client = Client("http://127.0.0.1:1", api_key="test")  # port 1 — should fail
        event = AssetMeasurement(
            asset_id="M-1", measurement_type="temperature", value=50, unit="°C",
        )

        with self.assertRaises(IaesClientError) as ctx:
            client.publish(event)

        self.assertIn("Connection failed", str(ctx.exception))

    # --- All 7 event types ---

    def test_publish_health_event(self):
        client = Client(self.base_url)
        event = AssetHealth(asset_id="M-1", health_index=0.42, source="test", severity="warning")
        result = client.publish(event)
        self.assertEqual(MockHandler.last_request_body["event_type"], "asset.health")

    def test_publish_work_order_intent(self):
        client = Client(self.base_url)
        event = WorkOrderIntent(
            asset_id="M-1",
            title="Replace bearing",
            priority="high",
            source="test",
        )
        result = client.publish(event)
        self.assertEqual(MockHandler.last_request_body["event_type"], "maintenance.work_order_intent")

    # --- Duplicate handling ---

    def test_duplicate_response(self):
        MockHandler.response_body = {
            "accepted": 1,
            "rejected": 0,
            "results": [{"event_id": "dup-1", "status": "duplicate"}],
        }
        client = Client(self.base_url)
        event = AssetMeasurement(
            asset_id="M-1", measurement_type="temperature", value=50, unit="°C",
        )
        result = client.publish(event)
        self.assertEqual(result["results"][0]["status"], "duplicate")


if __name__ == "__main__":
    main()

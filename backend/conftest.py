import os

# Test environment configuration
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("AUTH_SECRET_KEY", "mock-test-secret-key-at-least-32-chars-long")
os.environ.setdefault("DEMO_PASSWORD", "mock-test-demo-password")

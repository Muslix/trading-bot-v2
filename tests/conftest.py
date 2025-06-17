"""
Test Configuration for CI/CD Environments
Ensures proper setup for testing in environments without persistent storage
"""

import os
import tempfile
from pathlib import Path
import pytest


def setup_test_directories():
    """Setup test directories for CI/CD environments"""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    if not logs_dir.exists():
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            # Create empty error log file
            (logs_dir / "error.log").touch()
            print("✅ Created logs directory for testing")
        except (OSError, PermissionError):
            print("⚠️ Could not create logs directory, using console logging only")
    
    # Ensure required directories exist
    required_dirs = ["database", "config"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created {dir_name} directory for testing")
            except (OSError, PermissionError):
                print(f"⚠️ Could not create {dir_name} directory")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Automatically setup test environment before any tests run"""
    setup_test_directories()
    yield
    # Cleanup after tests if needed


def create_test_config():
    """Create a minimal test configuration"""
    
    # Create minimal .env file for testing if none exists
    env_files = [".env", ".env.local", ".env.test"]
    env_exists = any(Path(f).exists() for f in env_files)
    
    if not env_exists:
        test_env_content = """# Test environment configuration
TELEGRAM_BOT_TOKEN=test_token_123
TELEGRAM_CHAT_ID=123456789
ENVIRONMENT=test
DEBUG=true
"""
        try:
            with open(".env.test", "w") as f:
                f.write(test_env_content)
            print("✅ Created test environment configuration")
        except (OSError, PermissionError):
            print("⚠️ Could not create test environment file")


# Run setup when module is imported (for CI environments)
setup_test_directories()


if __name__ == "__main__":
    setup_test_directories()
    create_test_config()

"""Pytest configuration and fixtures."""

import pytest
import tempfile
import io
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    image = Image.new('RGB', (512, 512), color='red')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


@pytest.fixture
def sample_mask():
    """Create a sample test mask with transparency."""
    # Create RGBA mask with some transparent areas
    mask = Image.new('RGBA', (512, 512), (255, 255, 255, 0))
    
    # Draw some opaque areas (white areas to inpaint)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(mask)
    draw.rectangle([100, 100, 400, 400], fill=(255, 255, 255, 255))
    
    buffer = io.BytesIO()
    mask.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


@pytest.fixture
def invalid_image():
    """Create an invalid image file."""
    buffer = io.BytesIO(b"not an image")
    return buffer


@pytest.fixture
def oversized_image():
    """Create an oversized test image."""
    image = Image.new('RGB', (3000, 3000), color='blue')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

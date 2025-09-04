"""Tests for inpainting API endpoint."""

import pytest
import io
from fastapi.testclient import TestClient


def test_edit_rejects_missing_mask(client: TestClient, sample_image):
    """Test that /api/edit returns 422 when mask is missing."""
    files = {
        "image": ("test.png", sample_image, "image/png")
    }
    data = {
        "prompt": "test prompt"
    }
    
    response = client.post("/api/edit", files=files, data=data)
    
    assert response.status_code == 422
    error_detail = response.json()
    # FastAPI validation error format
    assert "detail" in error_detail
    assert any("mask" in str(item.get("loc", [])) for item in error_detail["detail"])


def test_edit_rejects_missing_image(client: TestClient, sample_mask):
    """Test that /api/edit returns 422 when image is missing."""
    files = {
        "mask": ("mask.png", sample_mask, "image/png")
    }
    data = {
        "prompt": "test prompt"
    }
    
    response = client.post("/api/edit", files=files, data=data)
    
    assert response.status_code == 422
    error_detail = response.json()
    # FastAPI validation error format
    assert "detail" in error_detail
    assert any("image" in str(item.get("loc", [])) for item in error_detail["detail"])


def test_edit_rejects_empty_prompt(client: TestClient, sample_image, sample_mask):
    """Test that /api/edit returns 422 when prompt is empty."""
    files = {
        "image": ("test.png", sample_image, "image/png"),
        "mask": ("mask.png", sample_mask, "image/png")
    }
    data = {
        "prompt": ""
    }
    
    response = client.post("/api/edit", files=files, data=data)
    
    assert response.status_code == 422


def test_edit_validates_prompt_length(client: TestClient, sample_image, sample_mask):
    """Test that /api/edit rejects prompts > 500 characters."""
    long_prompt = "a" * 501  # 501 characters
    
    files = {
        "image": ("test.png", sample_image, "image/png"),
        "mask": ("mask.png", sample_mask, "image/png")
    }
    data = {
        "prompt": long_prompt
    }
    
    response = client.post("/api/edit", files=files, data=data)
    
    assert response.status_code == 422


def test_edit_validates_seed_range(client: TestClient, sample_image, sample_mask):
    """Test that /api/edit validates seed parameter bounds."""
    files = {
        "image": ("test.png", sample_image, "image/png"),
        "mask": ("mask.png", sample_mask, "image/png")
    }
    data = {
        "prompt": "test prompt",
        "seed": -1  # Invalid seed
    }
    
    response = client.post("/api/edit", files=files, data=data)
    
    assert response.status_code == 422


def test_edit_returns_png_given_valid_image_and_mask(client: TestClient, sample_image, sample_mask):
    """Test that /api/edit returns PNG blob with valid inputs."""
    files = {
        "image": ("test.png", sample_image, "image/png"),
        "mask": ("mask.png", sample_mask, "image/png")
    }
    data = {
        "prompt": "a beautiful landscape",
        "strength": 0.7,
        "guidance_scale": 7.5
    }
    
    response = client.post("/api/edit", files=files, data=data)
    
    # Should return 200 with PNG content
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0
    
    # Check that it's actually a PNG file
    assert response.content.startswith(b'\x89PNG')
    
    # Check additional headers
    assert "X-Processing-Time" in response.headers


def test_edit_rejects_invalid_base64_image(client: TestClient, invalid_image, sample_mask):
    """Test that /api/edit returns 422 for malformed image."""
    files = {
        "image": ("invalid.png", invalid_image, "image/png"),
        "mask": ("mask.png", sample_mask, "image/png")
    }
    data = {
        "prompt": "test prompt"
    }
    
    response = client.post("/api/edit", files=files, data=data)
    
    assert response.status_code == 422


def test_edit_rejects_oversized_image(client: TestClient, oversized_image, sample_mask):
    """Test that /api/edit rejects images that are too large."""
    files = {
        "image": ("large.png", oversized_image, "image/png"),
        "mask": ("mask.png", sample_mask, "image/png")
    }
    data = {
        "prompt": "test prompt"
    }
    
    response = client.post("/api/edit", files=files, data=data)
    
    assert response.status_code == 422
    error_detail = response.json()
    assert "exceed" in error_detail["error_message"].lower()

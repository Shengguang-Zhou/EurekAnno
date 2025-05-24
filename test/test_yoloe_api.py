import base64
import io
import json
import os
from contextlib import ExitStack
from pathlib import Path

import pytest
import requests
from PIL import Image

DEFAULT_API_URL = "http://0.0.0.0:8000/api/v1/yoloe"
DEFAULT_IMAGE_PATH = "../dataset/examples/boys.jpeg"
DEFAULT_REFER_PATH = "../dataset/examples/boys.jpeg"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--api-url",
        action="store",
        default=os.getenv("YOLOE_API_URL", DEFAULT_API_URL),
        help="Base URL for the YOLOe API",
    )
    parser.addoption(
        "--image",
        action="store",
        default=os.getenv("YOLOE_IMAGE_PATH", DEFAULT_IMAGE_PATH),
        help="Path to the test image",
    )
    parser.addoption(
        "--refer",
        action="store",
        default=os.getenv("YOLOE_REFER_PATH", DEFAULT_REFER_PATH),
        help="Optional reference image path",
    )


@pytest.fixture
def api_url(request) -> str:
    return request.config.getoption("--api-url")


@pytest.fixture
def image_path(request) -> Path:
    return Path(request.config.getoption("--image"))


@pytest.fixture
def refer_path(request):
    value = request.config.getoption("--refer")
    return Path(value) if value else None


def send_image_prompt(api_url: str, image: Path, refer: Path | None) -> requests.Response:
    endpoint_url = f"{api_url}/image-prompt"
    bboxes = [[100, 100, 200, 200], [300, 300, 400, 400]]
    cls = [0, 1]
    data = {
        "bboxes": json.dumps(bboxes),
        "cls": json.dumps(cls),
        "return_image": "true",
        "conf": "0.25",
        "iou": "0.7",
        "retina_masks": "true",
    }
    with ExitStack() as stack:
        files = {"file": stack.enter_context(open(image, "rb"))}
        if refer:
            files["refer_file"] = stack.enter_context(open(refer, "rb"))
        response = requests.post(endpoint_url, files=files, data=data)
    return response


def test_image_prompt_endpoint(api_url: str, image_path: Path, refer_path: Path | None, tmp_path: Path) -> None:
    response = send_image_prompt(api_url, image_path, refer_path)
    assert response.status_code == 200

    result = response.json()
    assert "results" in result

    if "annotated_image" in result:
        image_data = base64.b64decode(result["annotated_image"])
        img = Image.open(io.BytesIO(image_data))
        img.save(tmp_path / "image_prompt_result.jpg")


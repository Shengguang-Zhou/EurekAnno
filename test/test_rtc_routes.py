import sys
import os
import types

sys.path.append(os.path.dirname(os.path.dirname(__file__)) or ".")

# Stub external dependencies so router modules can be imported without errors
cv2_stub = types.ModuleType('cv2')
cv2_stub.VideoCapture = lambda *a, **k: types.SimpleNamespace(read=lambda: (False, None), release=lambda: None)
cv2_stub.imencode = lambda ext, img: (True, b'')
cv2_stub.COLOR_RGB2BGR = 0
cv2_stub.cvtColor = lambda img, code: img
sys.modules['cv2'] = cv2_stub

np_stub = types.ModuleType('numpy')
np_stub.ndarray = object
np_stub.array = lambda *a, **k: []
sys.modules['numpy'] = np_stub

PIL_stub = types.ModuleType('PIL')
image_stub = types.ModuleType('PIL.Image')
image_stub.open = lambda stream: types.SimpleNamespace(convert=lambda mode: [])
sys.modules['PIL'] = PIL_stub
sys.modules['PIL.Image'] = image_stub

from fastapi import APIRouter
from fastapi.routing import APIWebSocketRoute
from app.api.rtc_yoloe import router as rtc_router


def test_routes():
    api_router = APIRouter()
    api_router.include_router(rtc_router, prefix="/api/v1/yoloe-stream")
    ws_paths = [route.path for route in api_router.routes if isinstance(route, APIWebSocketRoute)]
    expected = {
        "/api/v1/yoloe-stream/prompt-free",
        "/api/v1/yoloe-stream/text-prompt",
        "/api/v1/yoloe-stream/image-prompt",
    }
    assert expected.issubset(set(ws_paths)), f"Missing routes: {expected - set(ws_paths)}"


if __name__ == "__main__":
    test_routes()
    print("All RTC route tests passed.")

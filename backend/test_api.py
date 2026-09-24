"""
=============================================================================
KỊCH BẢN KIỂM THỬ TỰ ĐỘNG FASTAPI BACKEND (AUTOMATED API TESTS)
=============================================================================
Mục đích:
- Kiểm tra toàn bộ các HTTP REST API endpoints của FastAPI server.
- Kiểm thử các trường hợp dữ liệu hợp lệ (Happy Path) và dữ liệu sai (Validation).
- Chạy hoàn toàn tự động ở chế độ Giả lập (Simulation Mode), không phụ thuộc phần cứng.
- Không cần cài thêm bất kỳ thư viện ngoài nào (sử dụng thư viện chuẩn của Python).

Cách chạy:
    cd backend
    .\\venv\\Scripts\\python.exe test_api.py
=============================================================================
"""

import os
import sys
import time
import json
import threading
import urllib.request
import urllib.error

# Thiết lập encoding UTF-8 cho console Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Bật chế độ giả lập cho kịch bản test API
os.environ["CHROMA_SIMULATION"] = "1"

import uvicorn
from app.main import app

TEST_PORT = 8008
BASE_URL = f"http://127.0.0.1:{TEST_PORT}/api"

passed_tests = 0
failed_tests = 0

def log_test(test_name: str, passed: bool, detail: str = ""):
    global passed_tests, failed_tests
    if passed:
        passed_tests += 1
        print(f" [PASS] {test_name} {f'({detail})' if detail else ''}")
    else:
        failed_tests += 1
        print(f" [FAIL] {test_name} -> {detail}")

def http_get(endpoint: str):
    url = BASE_URL + endpoint
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def http_post(endpoint: str, data: dict):
    url = BASE_URL + endpoint
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def run_tests():
    global passed_tests, failed_tests
    print("\n" + "=" * 65)
    print(" BẮT ĐẦU KIỂM THỬ CÁC API ENDPOINTS FASTAPI (SIMULATION MODE)")
    print("=" * 65 + "\n")

    # 1. Test GET /api/idn
    status, body = http_get("/idn")
    log_test(
        "GET /api/idn - Nhận dạng thiết bị",
        status == 200 and "62050P" in body.get("device_id", ""),
        f"device_id: {body.get('device_id')}"
    )

    # 2. Test GET /api/error
    status, body = http_get("/error")
    log_test(
        "GET /api/error - Đọc tin nhắn lỗi hệ thống",
        status == 200 and "error" in body,
        f"error: {body.get('error')}"
    )

    # 3. Test POST /api/voltage (Hợp lệ: 24.5V)
    status, body = http_post("/voltage", {"voltage": 24.5})
    log_test(
        "POST /api/voltage - Cài đặt điện áp hợp lệ (24.5V)",
        status == 200 and body.get("voltage") == 24.5,
        f"voltage: {body.get('voltage')}V"
    )

    # 4. Test POST /api/voltage (Bảo vệ phần cứng: 150V > Max 100V)
    status, body = http_post("/voltage", {"voltage": 150.0})
    log_test(
        "POST /api/voltage - Chặn điện áp vượt định mức 100V",
        status == 422,  # HTTP 422 Unprocessable Entity
        f"Mã HTTP trả về: {status} (Đã chặn an toàn)"
    )

    # 5. Test POST /api/current (Hợp lệ: 5.0A)
    status, body = http_post("/current", {"current": 5.0})
    log_test(
        "POST /api/current - Cài đặt giới hạn dòng hợp lệ (5.0A)",
        status == 200 and body.get("current") == 5.0,
        f"current: {body.get('current')}A"
    )

    # 6. Test POST /api/current (Bảo vệ phần cứng: Dòng âm -2A)
    status, body = http_post("/current", {"current": -2.0})
    log_test(
        "POST /api/current - Chặn giới hạn dòng điện âm",
        status == 422,
        f"Mã HTTP trả về: {status} (Đã chặn an toàn)"
    )

    # 7. Test POST /api/output (Bật nguồn: 'ON')
    status, body = http_post("/output", {"state": "ON"})
    log_test(
        "POST /api/output - Bật ngõ ra ('ON')",
        status == 200 and body.get("output") == "ON",
        f"output: {body.get('output')}"
    )

    # 8. Test GET /api/telemetry (Đo lường tức thời khi ON)
    status, body = http_get("/telemetry")
    d = body.get("data", {})
    log_test(
        "GET /api/telemetry - Đọc dữ liệu đo thời gian thực",
        status == 200 and d.get("output_state") == "ON" and d.get("voltage_measured") == 24.5,
        f"{d.get('voltage_measured')}V | {d.get('current_measured')}A | {d.get('power_measured')}W"
    )

    # 9. Test POST /api/emergency-stop (Dừng khẩn cấp)
    status, body = http_post("/emergency-stop", {})
    # Kiểm tra sau khi dừng khẩn cấp thì ngõ ra phải OFF
    _, telem_after_stop = http_get("/telemetry")
    output_after = telem_after_stop.get("data", {}).get("output_state")
    log_test(
        "POST /api/emergency-stop - Ngắt ngõ ra khẩn cấp",
        status == 200 and output_after == "OFF",
        f"Trạng thái sau dừng: {output_after}"
    )

    # 10. Test POST /api/clear (*CLS)
    status, body = http_post("/clear", {})
    log_test(
        "POST /api/clear - Gửi lệnh xóa cờ lỗi (*CLS)",
        status == 200 and body.get("status") == "success",
        f"{body.get('message')}"
    )

    print("\n" + "=" * 65)
    print(f" KẾT QUẢ TỔNG HỢP: {passed_tests} PASS / {passed_tests + failed_tests} TỔNG SỐ TEST")
    if failed_tests == 0:
        print(" TẤT CẢ CÁC API HOẠT ĐỘNG HOÀN HẢO! 🎉")
    else:
        print(f" Có {failed_tests} bài test thất bại.")
    print("=" * 65 + "\n")

def main():
    # Khởi động server test ở luồng phụ (daemon)
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="127.0.0.1", port=TEST_PORT, log_level="error"),
        daemon=True
    )
    server_thread.start()
    time.sleep(1.5)  # Chờ server khởi động

    try:
        run_tests()
    finally:
        pass

if __name__ == "__main__":
    main()

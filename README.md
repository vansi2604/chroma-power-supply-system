# Web-based Power Supply Control System

Hệ thống điều khiển và giám sát máy nguồn một chiều **Chroma 62050P-100-100** thông qua giao diện Web cục bộ, sử dụng FastAPI (Backend) và Vanilla JS/HTML5 (Frontend) kết nối qua thư viện PyVISA.

---

## 1. Yêu cầu hệ thống
* **Hệ điều hành:** Windows (khuyên dùng để tương thích tốt nhất với Driver NI-VISA) hoặc Linux.
* **Python:** Phiên bản 3.9 trở lên (đã kiểm tra trên Python 3.12 / 3.14).
* **Phần cứng:** Máy nguồn Chroma 62050P-100-100 kết nối qua cổng USB (hoặc RS232/GPIB).
* **Driver:** Đã cài đặt **NI-VISA** (hoặc Keysight IO Libraries Suite) để hệ thống nhận diện giao thức USB-TMC.

---

## 2. Hướng dẫn Cài đặt & Cấu hình

### Bước 1: Clone mã nguồn về máy
```bash
git clone git@github.com:vansi2604/chroma-power-supply-system.git
cd chroma-power-control
```

Cấu trúc dự án:
```text
chroma-power-control/
├── backend/
│   ├── requirements.txt    # Danh sách thư viện Python cần thiết
│   ├── .venv/              # Môi trường ảo Python (tạo sau khi cài đặt)
│   └── ...                 # Mã nguồn backend (FastAPI, SCPI driver)
├── frontend/
│   ├── index.html          # Giao diện điều khiển Web
│   └── ...                 # Tệp CSS, JavaScript
├── README.md               # Tài liệu hướng dẫn
└── .gitignore
```

### Bước 2: Thiết lập môi trường Backend (Python Virtual Environment)

Di chuyển vào thư mục `backend`:
```bash
cd backend
```

Tạo môi trường ảo Python (`.venv`):
- **Sử dụng `venv` tiêu chuẩn:**
  ```bash
  python3 -m venv .venv
  ```
- **Hoặc sử dụng `uv` (nhanh hơn):**
  ```bash
  uv venv .venv
  ```

Kích hoạt môi trường ảo:
- **Trên Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```
- **Trên Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  *(Nếu gặp lỗi script execution policy trên PowerShell, chạy trước: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*
- **Trên Windows (Command Prompt - CMD):**
  ```cmd
  .venv\Scripts\activate.bat
  ```

Cài đặt các gói phụ thuộc:
- **Dùng pip:**
  ```bash
  pip install -r requirements.txt
  ```
- **Hoặc dùng uv:**
  ```bash
  uv pip install -r requirements.txt
  ```

### Bước 3: Kiểm tra nhận diện thiết bị Chroma (PyVISA)

Sau khi cài đặt xong thư viện và cắm cáp USB nối máy nguồn với máy tính, kiểm tra xem hệ thống đã nhận diện được thiết bị chưa:
```bash
python -c "import pyvisa; rm = pyvisa.ResourceManager(); print('Devices found:', rm.list_resources())"
```
Thông tin thiết bị trả về thường có định dạng dạng:
`USB0::0x0A2D::...::INSTR`

---

## 3. Hướng dẫn Khởi chạy Hệ thống

### 1. Khởi động Backend (FastAPI API Server)
Tại thư mục `backend`, đảm bảo môi trường ảo đã được kích hoạt:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Server API sẽ chạy tại: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Tài liệu kiểm thử API tương tác (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Tài liệu API ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

#### Các API Endpoints chính:
- `GET /api/idn`: Nhận diện thiết bị phần cứng (*IDN?).
- `GET /api/telemetry`: Đọc đo lường thời gian thực (Volt thực tế, Amp thực tế, Watt tức thời, trạng thái Output).
- `POST /api/voltage`: Cài đặt điện áp ngõ ra (0V - 100V).
- `POST /api/current`: Cài đặt giới hạn dòng điện (0A - 100A).
- `POST /api/output`: Bật/Tắt ngõ ra (`ON` / `OFF`).
- `POST /api/emergency-stop`: Dừng khẩn cấp ngắt ngõ ra ngay lập tức và xóa lỗi (*CLS).

### 2. Khởi động Frontend (Giao diện Web)
Có thể mở giao diện bằng một trong các cách sau:

- **Cách 1: Chạy Local Web Server (Khuyên dùng)**
  Mở terminal mới, chuyển vào thư mục `frontend` và chạy máy chủ HTTP tĩnh:
  ```bash
  cd frontend
  python3 -m http.server 3000
  ```
  Sau đó mở trình duyệt và truy cập: [http://localhost:3000](http://localhost:3000)

- **Cách 2: Sử dụng VS Code Live Server**
  Mở tệp `frontend/index.html` trong VS Code, click chuột phải chọn **"Open with Live Server"**.

- **Cách 3: Mở trực tiếp file HTML**
  Mở trực tiếp tệp `frontend/index.html` bằng trình duyệt web (Chrome, Edge, Firefox).

---

## 4. Xử lý sự cố thường gặp (Troubleshooting)

1. **Lỗi `VisaIOError` hoặc không tìm thấy thiết bị (`Devices found: ()`):**
   - Đảm bảo máy nguồn Chroma đã được bật nguồn và cáp USB cắm chắc chắn.
   - Kiểm tra Driver **NI-VISA Runtime** đã được cài đặt trên máy.
   - Trên **Windows**: Mở *NI MAX (Measurement & Automation Explorer)* hoặc *Device Manager* xem thiết bị USB Test & Measurement Device (USBTMC) có nhận diện không.
   - Trên **Linux**: Cần phân quyền truy cập USB cho người dùng (udev rules):
     ```bash
     # Thêm rule cho USBTMC (ví dụ)
     echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0a2d", MODE="0666"' | sudo tee /etc/udev/rules.d/99-chroma.rules
     sudo udevadm control --reload-rules && sudo udevadm trigger
     ```

2. **Lỗi `Port 8000 already in use`:**
   - Cổng 8000 đang bị ứng dụng khác chiếm giữ. Bạn có thể đổi cổng khi chạy uvicorn:
     ```bash
     uvicorn main:app --reload --port 8080
     ```

3. **Lỗi CORS khi gọi API từ Frontend:**
   - Đảm bảo Backend FastAPI đã cấu hình `CORSMiddleware` cho phép origin của frontend (`http://localhost:3000` hoặc `*`).
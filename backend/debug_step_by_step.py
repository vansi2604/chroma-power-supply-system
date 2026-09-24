"""
=============================================================================
KỊCH BẢN DEBUG TỪNG BƯỚC (STEP-BY-STEP HARDWARE DIAGNOSTIC)
=============================================================================
Chạy kịch bản này để chẩn đoán chính xác tầng nào trong kết nối đang bị lỗi:
- Tầng 1: Driver & PyVISA backend
- Tầng 2: Nhận diện cổng USB
- Tầng 3: Mở phiên kết nối (open_resource)
- Tầng 4: Ghi lệnh xuống cổng USB (viWrite)
- Tầng 5: Đọc phản hồi từ máy nguồn (viRead)
=============================================================================
"""

import sys
import time

# Đảm bảo in tiếng Việt trên console Windows không lỗi font
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pyvisa

VISA_ADDR = "USB0::0x1698::0x0837::008000000304::INSTR"

def step(title):
    print(f"\n{'='*60}\n--> {title}\n{'='*60}")

def run_debug():
    print("CHƯƠNG TRÌNH DEBUG KẾT NỐI MÁY NGUỒN CHROMA 62050P-100-100")
    print(f"Địa chỉ mục tiêu: {VISA_ADDR}\n")

    # ----------------------------------------------------
    # BƯỚC 1: Kiểm tra NI-VISA Backend
    # ----------------------------------------------------
    step("BƯỚC 1: Kiểm tra PyVISA và Driver NI-VISA trên Windows")
    try:
        rm = pyvisa.ResourceManager()
        print(f"[OK] Đã tải thành công thư viện VISA: {rm}")
    except Exception as e:
        print(f"[THẤT BẠI] Lỗi khởi tạo PyVISA: {e}")
        return

    # ----------------------------------------------------
    # BƯỚC 2: Kiểm tra danh sách thiết bị nhận diện được
    # ----------------------------------------------------
    step("BƯỚC 2: Quét danh sách thiết bị trên cổng USB")
    try:
        devices = rm.list_resources()
        print(f"Các thiết bị tìm thấy: {devices}")
        if VISA_ADDR in devices:
            print(f"[OK] Thiết bị Chroma {VISA_ADDR} có mặt trong hệ thống!")
        else:
            print(f"[THẤT BẠI] Không tìm thấy {VISA_ADDR} trong danh sách.")
            return
    except Exception as e:
        print(f"[THẤT BẠI] Lỗi quét thiết bị: {e}")
        return

    # ----------------------------------------------------
    # BƯỚC 3: Mở phiên làm việc cấp thấp (Open Resource)
    # ----------------------------------------------------
    step("BƯỚC 3: Mở phiên giao tiếp cấp thấp (open_resource)")
    inst = None
    try:
        inst = rm.open_resource(VISA_ADDR)
        inst.timeout = 2000  # 2 giây
        print(f"[OK] Đã mở thành công session VISA: {inst}")
        print(f"     Interface type : {inst.interface_type}")
        print(f"     Resource class : {inst.resource_class}")
        print(f"     Timeout mặc định: {inst.timeout} ms")
    except Exception as e:
        print(f"[THẤT BẠI] Không thể mở session: {e}")
        return

    # ----------------------------------------------------
    # BƯỚC 4: Kiểm tra khả năng GHI (viWrite) xuống USB
    # ----------------------------------------------------
    step("BƯỚC 4: Thử nghiệm gửi dữ liệu (viWrite) qua USB")
    # Thử gửi 1 byte LineFeed đơn giản
    try:
        print("-> Đang thử gửi byte LF (\\n) thô...")
        count = inst.write_raw(b"\n")
        print(f"[OK] Gửi thành công {count} bytes xuống cổng USB!")
    except Exception as e:
        print(f"[THẤT BẠI BƯỚC 4] Lệnh GHI bị lỗi: {type(e).__name__} -> {e}")
        print("-> NGUYÊN NHÂN: Chip USB trên máy Chroma đang từ chối nhận dữ liệu (USB NAK/Stall).")
        inst.close()
        return

    # ----------------------------------------------------
    # BƯỚC 5: Thử nghiệm gửi lệnh truy vấn *IDN?
    # ----------------------------------------------------
    step("BƯỚC 5: Thử nghiệm gửi lệnh *IDN? và đọc phản hồi")
    try:
        print("-> Đang gửi lệnh: *IDN?\\n ...")
        inst.write_raw(b"*IDN?\n")
        time.sleep(0.1) # Chờ 100ms cho máy xử lý

        print("-> Đang chờ đọc phản hồi từ máy Chroma...")
        raw_resp = inst.read_raw()
        print(f"[THÀNH CÔNG RỰC RỠ] Phản hồi nhận được: {raw_resp.decode('utf-8', errors='ignore').strip()}")
    except pyvisa.errors.VisaIOError as e:
        print(f"[THẤT BẠI BƯỚC 5] Lỗi đọc phản hồi: {e}")
        if "VI_ERROR_TMO" in str(e):
            print("\n" + "-"*60)
            print("CHẨN ĐOÁN NGUYÊN NHÂN:")
            print("1. Máy tính đã GỬI được lệnh '*IDN?' qua cáp USB thành công.")
            print("2. Nhưng máy Chroma KHÔNG trả lời (Timeout).")
            print("Điều này chứng minh:")
            print("- Dây cáp USB và driver máy tính hoàn toàn hoạt động tốt!")
            print("- Vấn đề nằm ở cấu hình bên trong máy nguồn Chroma:")
            print("  + Hoặc trên máy Chroma chưa bật Remote Mode (cần bấm nút LOCAL/REMOTE).")
            print("  + Hoặc trong Menu máy Chroma chưa chọn Interface = USB (đang để RS232/GPIB).")
            print("  + Hoặc máy Chroma đang kẹt màn hình cài đặt tham số.")
            print("-"*60)
    except Exception as e:
        print(f"[THẤT BẠI BƯỚC 5] Lỗi khác: {e}")
    finally:
        if inst:
            inst.close()
        rm.close()

if __name__ == "__main__":
    run_debug()

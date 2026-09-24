Dưới đây là **Bộ tài liệu tra cứu lệnh SCPI chuẩn (SCPI Reference Manual)** được hiệu chỉnh trực tiếp theo thông số kỹ thuật của model **Chroma 62050P-100-100** từ tài liệu hãng.

---

### 1. Thông số giới hạn định mức (Model 62050P-100-100)

* **Điện áp ra cực đại (\\(V_{max}\\))**: **100.0 V** (Dải cài đặt: `0.0` đến `100.0` V).
* **Dòng điện ra cực đại (\\(I_{max}\\))**: **100.0 A** (Dải cài đặt: `0.0` đến `100.0` A).
* **Công suất cực đại (\\(P_{max}\\))**: **5000 W** (5 kW).
* **Tốc độ tăng/giảm điện áp (Voltage Slew Rate)**: `0.001` đến `10.0` V/ms.
* **Tốc độ tăng/giảm dòng điện (Current Slew Rate)**: `0.001` đến `1.0` A/ms.

---

### 2. Bảng tra cứu lệnh SCPI chuẩn cho Chroma 62050P-100-100

| Nhóm chức năng | Cú pháp SCPI (Dạng ngắn) | Cú pháp đầy đủ | Dải giá trị / Ví dụ phản hồi | Mô tả chi tiết |
| :--- | :--- | :--- | :--- | :--- |
| **🔍 Kiểm tra kết nối** | `*IDN?` | `*IDN?` | `CHROMA,62050P-100-100,01.00,2005/07/14` | Đọc chuỗi định danh nhà sản xuất và model. |
| **🧹 Xóa bộ nhớ lỗi** | `*CLS` | `*CLS` | *(Không trả về chuỗi)* | Xóa sạch bộ nhớ trạng thái và mã lỗi cũ. |
| **⚡ Cài đặt điện áp** | `SOUR:VOLT <value>` | `SOURce:VOLTage <value>` | `SOUR:VOLT 50.0` | Đặt điện áp đầu ra (0.0 – 100.0 V). |
| **🔍 Đọc điện áp đã cài** | `SOUR:VOLT?` | `SOURce:VOLTage?` | `5.000000e+01` | Trả về giá trị điện áp đang cài đặt. |
| **🔌 Cài giới hạn dòng** | `SOUR:CURR <value>` | `SOURce:CURRent <value>` | `SOUR:CURR 10.0` | Đặt giới hạn dòng điện (0.0 – 100.0 A). |
| **🔍 Đọc dòng đã cài** | `SOUR:CURR?` | `SOURce:CURRent?` | `1.000000e+01` | Trả về giá trị dòng điện đang cài đặt. |
| **🟢 Bật Output** | `CONF:OUTP ON` *(hoặc `1`)* | `CONFigure:OUTPut ON` | *(Không trả về chuỗi)* | Bật đầu ra công suất. |
| **🔴 Tắt Output** | `CONF:OUTP OFF` *(hoặc `0`)* | `CONFigure:OUTPut OFF` | *(Không trả về chuỗi)* | Ngắt đầu ra công suất. |
| **🔎 Trạng thái Output** | `CONF:OUTP?` | `CONFigure:OUTPut?` | `1` (Đang ON) hoặc `0` (Đang OFF) | Truy vấn trạng thái bật/tắt đầu ra. |
| **🛡️ Cài bảo vệ quá áp** | `SOUR:VOLT:PROT:HIGH <V>` | `SOURce:VOLTage:PROTect:HIGH` | `SOUR:VOLT:PROT:HIGH 105.0` | Cài ngưỡng OVP (tối đa 110V). |
| **🛡️ Cài bảo vệ quá dòng** | `SOUR:CURR:PROT:HIGH <I>` | `SOURce:CURRent:PROTect:HIGH` | `SOUR:CURR:PROT:HIGH 102.0` | Cài ngưỡng OCP (tối đa 105A). |
| **🛡️ Cài bảo vệ quá công suất**| `SOUR:POW:PROT:HIGH <P>`| `SOURce:POWer:PROTect:HIGH` | `SOUR:POW:PROT:HIGH 5250` | Cài ngưỡng OPP (tối đa 5250W). |
| **📈 Cài Slew Rate điện áp**| `SOUR:VOLT:SLEW <value>` | `SOURce:VOLTage:SLEW <value>` | `SOUR:VOLT:SLEW 1.0` | Đặt tốc độ thay đổi điện áp (V/ms). |
| **📈 Cài Slew Rate dòng** | `SOUR:CURR:SLEW <value>` | `SOURce:CURRent:SLEW <value>` | `SOUR:CURR:SLEW 0.1` | Đặt tốc độ thay đổi dòng điện (A/ms). |
| **📊 Đo nhanh (Buffer)** | `FETC:VOLT?` / `FETC:CURR?` | `FETCh:VOLTage?` / `CURRent?` | `50.01` (V) / `10.02` (A) | Đọc dữ liệu đo thực tế tốc độ cao (~10ms). |
| **📊 Đo trực tiếp** | `MEAS:VOLT?` / `MEAS:CURR?` | `MEASure:VOLTage?` / `CURRent?` | `50.01` (V) / `10.02` (A) | Đo trực tiếp tại đầu ra (~70ms). |
| **📊 Đo công suất** | `FETC:POW?` *(hoặc `MEAS:POW?`)*| `FETCh:POWer?` | `501.10` (Đơn vị Watt) | Đọc công suất thực tế xuất ra. |
| **⚠️ Đọc trạng thái máy** | `FETC:STAT?` | `FETCh:STATus?` | Mã trạng thái hệ thống | Kiểm tra lỗi/chế độ hoạt động. |

---

### 3. Quy tắc lập trình & định dạng truyền dữ liệu

1. **Cú pháp Bật/Tắt Output**: Chuẩn của Chroma 62000P bắt buộc dùng cấu trúc `CONFigure:OUTPut` (viết tắt `CONF:OUTP ON` hoặc `CONF:OUTP OFF`).
2. **Ký tự kết thúc (Terminator)**: Mọi chuỗi lệnh gửi xuống máy bắt buộc có ký tự Line Feed **`\n`** (ASCII `0x0A`).
3. **Gộp nhiều lệnh**: Có thể dùng dấu chấm phẩy `;` để truyền nhiều lệnh trên một dòng nhằm tối ưu tốc độ.
   * *Ví dụ*: `SOUR:VOLT 48.0;CURR 50.0\n`
   * *Ví dụ đọc nhanh V, I, P*: `FETC:VOLT?;CURR?;POW?\n`
4. **Tốc độ truy vấn dữ liệu**: Nên dùng nhóm lệnh `FETC` (`FETC:VOLT?`, `FETC:CURR?`) cho vòng lặp Monitoring/Polling trên Web UI vì thời gian phản hồi chỉ tốn **~10ms**, nhanh hơn so với `MEAS` (**~70ms**).

---

### 4. Luồng xử lý Backend khuyến nghị (Pseudo Flow)

```text
[Khởi tạo kết nối USB / Virtual COM]
  1. Open Serial Port (Baudrate mặc định: 9600, Data bits: 8, Stop bits: 1, Parity: None)
  2. Send: "*IDN?\n"
  3. Read -> Kiểm tra chuỗi trả về chứa "62050P-100-100"

[Cấu hình thông số & Bật nguồn]
  4. Send: "*CLS\n"                      (Xóa bộ nhớ lỗi cũ)
  5. Send: "SOUR:VOLT 24.0;CURR 20.0\n" (Đặt 24V và giới hạn 20A)
  6. Send: "CONF:OUTP ON\n"             (Bật đầu ra)

[Vòng lặp Polling dữ liệu Web UI (Mỗi 100ms - 200ms)]
  7. Send: "FETC:VOLT?;CURR?;POW?\n"
  8. Read & Parse kết quả hiển thị lên màn hình

[Tắt nguồn an toàn khi Stop / Đóng ứng dụng]
  9. Send: "CONF:OUTP OFF\n"            (Ngắt đầu ra)
 10. Close Serial Port
```

---

🔌 *Bạn có cần mình viết sẵn đoạn code mẫu kết nối và gửi luồng lệnh này bằng Node.js (dùng package `serialport`) hoặc Python (dùng `pyserial`) không?*
# Aut0Secure

> Discord Bot tự động bảo mật tài khoản Microsoft & Minecraft, tích hợp mail server bắt OTP tự động, kiểm tra Hypixel/DonutSMP và tạo ảnh thống kê (hit card).

---

## Tính năng chính

- **Core Securing Engine**: Tự động đổi email bảo mật, mật khẩu, xóa 2FA/thiết bị cũ, rời nhóm gia đình (family), tạo Recovery Code & TOTP secret.
- **Thao tác đơn lẻ & Hàng loạt (Bulk)**: Hỗ trợ nhập tài khoản đơn hoặc xử lý danh sách lớn qua giao diện Discord Modals & Buttons.
- **Tích hợp Mail Server & OTP Bridge**: Tự động nhận email qua SMTP nội bộ (port 25) và trích xuất mã OTP tức thì về Discord webhook.
- **Minecraft Checker & Card Render**: Kiểm tra trạng thái ban, rank, stats trên Hypixel và DonutSMP; tự động render card kết quả dạng ảnh PNG.
- **Quản trị trực quan**: Bảng điều khiển admin (`/menu`), phân quyền Owner, cấu hình kênh logs và quản lý credits.

---

## 🛠️ Yêu cầu & Cài đặt

- **Python**: 3.10 trở lên
- **Hệ điều hành**: Windows hoặc Linux

```bash
# 1. Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# 2. Khởi tạo file cấu hình (nếu chưa có)
cp config/config.json.example config/config.json
cp config/bot.json.example config/bot.json
```

---

## ⚙️ Thiết lập cấu hình (`config/config.json`)

Mở file `config/config.json` và cập nhật các thông tin cơ bản:

| Mục | Mô tả |
| :--- | :--- |
| `owners` | Danh sách Discord User ID của các Admin sở hữu bot |
| `tokens.bot_token` | Token Discord Bot (lấy tại [Discord Developer Portal](https://discord.com/developers/applications)) |
| `tokens.skytools_key` | API Key Skytools (dùng kiểm tra dữ liệu Hypixel) |
| `tokens.donut_key` | API Key DonutSMP |
| `discord.*_channel` | ID các kênh nhận logs, accounts và censored logs |
| `autosecure` | Luật lọc & bảo mật (bật/tắt 2FA, đổi alias, từ chối tài khoản family/gamepass/underage) |
| `coldproxy` / `proxy` | Cấu hình proxy luân chuyển IP tránh rate limit |

---

## 🚀 Khởi chạy

### Trên Windows
```powershell
.\start.ps1
# hoặc chạy trực tiếp:
py bot.py
```

### Trên Linux
```bash
# Chạy trực tiếp qua script
chmod +x start.sh
./start.sh

# Hoặc chạy nền bằng PM2
pm2 start ecosystem.config.cjs
```

---

## 📁 Cấu trúc dự án

```
Aut0Secure/
├── bot.py               # Điểm khởi chạy chính của bot Discord
├── cogs/                # Các slash commands & module mở rộng (menu, secure, stats, email,...)
├── config/              # Cấu hình bot & module cached config
├── database/            # SQLite connection (WAL mode) và dữ liệu tài khoản
├── mail/                # SMTP Server nội bộ (port 25) & forward OTP
├── minecraft/           # Module check Hypixel, DonutSMP & ban status
├── securing/            # Core logic xử lý bảo mật tài khoản Microsoft
├── shared/              # Helper render hit card, gửi logs & embed
├── ui/                  # Giao diện Discord tương tác (Buttons & Modals)
├── start.ps1 / start.sh # Script giải phóng port và chạy bot tự động
└── ecosystem.config.cjs # Cấu hình chạy production qua PM2
```
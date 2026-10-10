# OKR Scale – bộ module OKR cho Odoo 17 Community

Bộ add-on quản trị mục tiêu theo OKR (Objectives & Key Results) cho Odoo 17
Community, dựng mới từ đầu, tách module để cài đặt và nâng cấp độc lập.

| Module | Chức năng | Phụ thuộc |
|---|---|---|
| `okr_scale` | Lõi: chu kỳ, mục tiêu 3 cấp, KR, căn chỉnh, check-in, duyệt, chấm điểm, phân quyền theo sơ đồ tổ chức (ứng dụng Nhân viên), Không gian OKR cá nhân, Dashboard tổng, Bảng xếp hạng | `hr`, `mail`, `web_hierarchy` |
| `okr_scale_project` | Liên kết KR với Dự án / Nhiệm vụ, tiến độ KR tự đồng bộ từ nhiệm vụ | `okr_scale`, `project` |
| `okr_scale_cfr` | CFR: Trao đổi 1:1, Phản hồi minh bạch (ẩn danh chỉ khi bật trong Thiết lập), Bảng ghi nhận / lời khen, Giá trị cốt lõi | `okr_scale`, `calendar` |
| `okr_scale_reward` | Điểm thưởng (sổ cái), ngân sách tặng điểm hàng tháng, điểm tự động, Cửa hàng đổi quà | `okr_scale_cfr`, `product` |
| `okr_scale_reward_stock` | Quản lý quà tặng qua Kho: sản phẩm lưu kho, phiếu xuất khi duyệt đổi quà, cho phép đặt trước khi chưa có hàng | `okr_scale_reward`, `stock` |
| `okr_scale_portal` | Chia sẻ OKR cho từng tài khoản portal (khách hàng B2B) với quyền Chỉ xem / Có thể cập nhật, như Project | `okr_scale`, `portal` |
| `dmag_brand_theme` | Màu nhận diện DMAG cho toàn bộ giao diện Odoo (tùy chọn) | `web` |

## Cài đặt

1. Thêm thư mục repo vào `addons_path` của Odoo 17.
2. *Ứng dụng > Cập nhật danh sách ứng dụng*, tìm **OKR Scale** và cài các module cần dùng.
3. Bật tiếng Việt: *Thiết lập > Ngôn ngữ* (các module có sẵn bản dịch `vi`).

## Phát triển & kiểm thử

```bash
odoo-bin -c odoo.conf -d test_okr -i okr_scale,okr_scale_project,okr_scale_cfr,okr_scale_reward,okr_scale_reward_stock,okr_scale_portal \
  --test-tags /okr_scale,/okr_scale_project,/okr_scale_cfr,/okr_scale_reward,/okr_scale_reward_stock,/okr_scale_portal --stop-after-init
```

Nguyên tắc để dễ nâng cấp lên Odoo 18/19: chỉ dùng kế thừa chuẩn (`_inherit`,
XPath, OWL registry), không sửa core Odoo; các module mở rộng gắn vào lõi qua
các hook có sẵn (`_compute_progress_by_method`, `_notify_checkin_due`,
`okr.scale.dashboard._get_extra_kpis / _get_extra_sections`).

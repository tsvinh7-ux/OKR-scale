=========
OKR Scale
=========

Module lõi quản trị mục tiêu theo phương pháp OKR cho Odoo 17 Community.

Tính năng
=========

* **Chu kỳ OKR**: năm / quý / tùy chỉnh, chu kỳ con nằm trong chu kỳ cha,
  tần suất check-in (hàng tuần, 2 tuần, hàng tháng), bật/tắt quy trình duyệt.
* **Mục tiêu 3 cấp**: Công ty, Phòng ban, Cá nhân. Mục tiêu cấp dưới được
  *căn chỉnh* vào một Kết quả then chốt (KR) của cấp trên.
* **Kết quả then chốt**: kiểu số, %, số tiền, đạt/không đạt; giá trị đầu,
  đích, hiện tại (hỗ trợ cả mục tiêu *giảm*, ví dụ giảm tỷ lệ khiếu nại);
  trọng số; đo tiến độ **thủ công** (qua check-in) hoặc **từ các mục tiêu
  căn chỉnh** (tự tổng hợp từ cấp dưới). Module ``okr_scale_project`` bổ sung
  cách đo theo nhiệm vụ dự án.
* **Check-in**: giá trị mới, mức độ tự tin 1-10, tâm trạng, kết quả đạt được,
  vướng mắc, kế hoạch kỳ tới; quản lý xem và phản hồi. Nhắc check-in tự
  động (activity) khi quá hạn theo tần suất của chu kỳ.
* **Trạng thái tự động**: Đúng tiến độ / Có rủi ro / Chậm tiến độ / Đã đạt,
  kết hợp giữa tiến độ thực tế so với thời gian đã trôi qua và mức độ tự tin.
* **Quy trình**: Nháp → Chờ duyệt → Đang thực hiện → Đã đóng (chấm điểm
  0.0-1.0, tự đánh giá, bài học kinh nghiệm). Đóng chu kỳ sẽ chấm điểm toàn
  bộ mục tiêu đang chạy.
* **Khóa cam kết**: khi mục tiêu đang chạy, người phụ trách không tự sửa
  được đích / trọng số / cách đo của KR, chỉ quản lý mới sửa được.
* **Giao diện**: kanban, danh sách, sơ đồ cây OKR (hierarchy), pivot, biểu đồ,
  **Dashboard tổng** (lọc theo chu kỳ, phòng ban).

Phân quyền
==========

======================  ===================================================
Nhóm                    Quyền
======================  ===================================================
Người dùng (mọi nhân    Xem OKR được phép xem; tạo/sửa OKR **cá nhân** của
viên, tự động)          mình; check-in KR mình phụ trách.
Quản lý                 Toàn quyền OKR **phòng ban** mình quản lý (và phòng
                        ban con), OKR cá nhân của nhân viên cấp dưới; duyệt
                        mục tiêu, phản hồi check-in.
Quản trị OKR            Chu kỳ, OKR **công ty**, toàn bộ OKR.
======================  ===================================================

Quan hệ quản lý được lấy từ **Nhân viên** (trường Quản lý) và **Phòng ban**
(trường Quản lý, tính cả phòng ban cha).

Phạm vi hiển thị của từng mục tiêu:

* *Mọi người*: toàn công ty xem được.
* *Phòng ban*: thành viên phòng ban của mục tiêu.
* *Người phụ trách và quản lý*: chỉ người phụ trách, người phụ trách KR và
  các cấp quản lý.

Quản trị OKR và các cấp quản lý luôn xem được OKR của cấp dưới.

Cấu hình
========

1. Thiết lập **Phòng ban** và **Nhân viên** (liên kết với người dùng, quản lý).
2. *OKR > Cấu hình > Chu kỳ*: tạo chu kỳ năm và các quý, bấm *Bắt đầu chu kỳ*.
3. Quản trị OKR tạo mục tiêu công ty; quản lý phòng ban căn chỉnh mục tiêu
   phòng ban vào KR công ty; nhân viên căn chỉnh mục tiêu cá nhân.

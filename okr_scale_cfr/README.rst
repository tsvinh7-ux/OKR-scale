===============
OKR Scale - CFR
===============

Phân hệ **CFR** (Conversations - Feedback - Recognition: Trao đổi, Phản hồi, Ghi nhận)
bổ sung cho phân hệ lõi ``okr_scale`` các công cụ quản trị hiệu suất liên tục xoay quanh OKR.

Tính năng
=========

Bảng ghi nhận (Lời khen / Kudos)
--------------------------------
* Gửi lời khen tới một hoặc nhiều đồng nghiệp (chỉ người dùng nội bộ), gắn với
  **giá trị cốt lõi** của công ty và tuỳ chọn liên kết tới một mục tiêu / kết quả then chốt.
* Hai chế độ hiển thị: *Mọi người* (hiện trên bảng ghi nhận chung) hoặc *Người gửi và người nhận*.
* Người nhận được thông báo ngay khi lời khen được tạo; không thể tự khen chính mình.
* Nút **Thích / Bỏ thích** cho mọi người xem được lời khen.
* Nút **Gửi lời khen** trên biểu mẫu mục tiêu (người nhận mặc định là người phụ trách mục tiêu và các KR)
  và nút thống kê *Lời khen*.

Phản hồi
--------
* Phản hồi chủ động hoặc theo yêu cầu (menu *Xin phản hồi*): người yêu cầu chọn những người
  sẽ phản hồi, mỗi người nhận được một hoạt động (activity) để trả lời.
* Ba loại phản hồi: Khen ngợi, Góp ý xây dựng, Đề xuất.
* **Phản hồi ẩn danh**: người nhận không bao giờ thấy người viết.

  - Trường ``author_id`` chỉ đọc được bởi nhóm *Quản trị OKR*; người dùng khác thấy trường
    tính toán ``author_display`` ("Ẩn danh").
  - Model không có cột ``create_uid`` / ``write_uid``; thông báo gửi tới người nhận được đăng
    bởi OdooBot và người viết không được thêm vào danh sách theo dõi.

Trao đổi 1:1
------------
* Quản lý (nhóm *Quản lý OKR*) tạo buổi trao đổi với nhân viên, chọn các mục tiêu cần thảo luận.
* Chương trình mặc định gồm các câu hỏi: tiến độ OKR, vướng mắc, hỗ trợ cần thiết, sự nghiệp và phát triển.
* Ghi chú, việc cần làm, nút **Lên lịch họp** tạo sự kiện lịch với cả hai người tham gia
  (đổi ngày/thời lượng buổi trao đổi sẽ cập nhật sự kiện) và nút **Đánh dấu hoàn thành**.

Bảng điều khiển
---------------
* Chỉ số *Lời khen (chu kỳ này)* và bảng *Người được ghi nhận nhiều nhất* trong khoảng thời gian của chu kỳ.

Phân quyền
==========
* Lời khen công khai: mọi người dùng OKR xem được; lời khen riêng tư: người gửi, người nhận và quản trị OKR.
  Chỉ người gửi (hoặc quản trị OKR) được sửa / xoá.
* Phản hồi: người viết, người nhận, người yêu cầu và quản trị OKR xem được; người viết chỉ sửa khi
  phản hồi còn ở trạng thái Nháp / Đã yêu cầu.
* Trao đổi 1:1: chỉ hai người tham gia và quản trị OKR; quản lý OKR mới được tạo.
* Quy tắc đa công ty cho các model có ``company_id``.

Cấu hình
========
*OKR > Cấu hình > Giá trị cốt lõi*: 5 giá trị mặc định (Khách hàng là trên hết, Tinh thần làm chủ,
Tinh thần đồng đội, Đổi mới sáng tạo, Chính trực) có thể chỉnh sửa.

Tác giả
=======
DMAG - Giấy phép LGPL-3

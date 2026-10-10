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
* Giao diện bảng ghi nhận theo nhận diện DMAG: banner (số lời khen trong tháng, bạn nhận / bạn gửi,
  giá trị được thể hiện nhiều nhất, nút **Gửi lời khen**), thẻ lời khen với ảnh người gửi -> người nhận,
  lời khen dạng trích dẫn, giá trị cốt lõi kèm biểu tượng, điểm thưởng (vàng) và nút thích.

Phản hồi
--------
* Phản hồi chủ động hoặc theo yêu cầu (menu *Xin phản hồi*): người yêu cầu chọn những người
  sẽ phản hồi, mỗi người nhận được một hoạt động (activity) để trả lời.
* Ba loại phản hồi: Khen ngợi, Góp ý xây dựng, Đề xuất.
* **Minh bạch là mặc định**: trong OKR không có phản hồi ẩn danh - mọi phản hồi đều hiển thị
  người viết. Ô *Ẩn danh* bị ẩn và ràng buộc dữ liệu chặn ``anonymous = True``.
* **Phản hồi ẩn danh (tuỳ chọn)**: quản trị viên có thể bật *Cho phép phản hồi ẩn danh* trong
  *Cài đặt > OKR > Phản hồi* (tham số ``okr_scale_cfr.allow_anonymous_feedback``, mặc định tắt).
  Khi được bật, người nhận không bao giờ thấy người viết:

  - Trường ``author_id`` chỉ đọc được bởi nhóm *Quản trị OKR*; người dùng khác thấy trường
    tính toán ``author_display`` ("Ẩn danh").
  - Model không có cột ``create_uid`` / ``write_uid``; thông báo gửi tới người nhận được đăng
    bởi OdooBot và người viết không được thêm vào danh sách theo dõi.
  - Nếu tắt lại tuỳ chọn, phản hồi ẩn danh còn ở trạng thái nháp phải bỏ chọn *Ẩn danh* trước khi gửi;
    các phản hồi ẩn danh đã gửi vẫn được bảo vệ như cũ.

Trao đổi 1:1
------------
* Quản lý (nhóm *Quản lý OKR*) tạo buổi trao đổi với nhân viên, chọn các mục tiêu cần thảo luận.
* Chương trình mặc định gồm các câu hỏi: tiến độ OKR, vướng mắc, hỗ trợ cần thiết, sự nghiệp và phát triển.
* Ghi chú, việc cần làm, nút **Lên lịch họp** tạo sự kiện lịch với cả hai người tham gia
  (đổi ngày/thời lượng buổi trao đổi sẽ cập nhật sự kiện) và nút **Đánh dấu hoàn thành**.

Bảng điều khiển
---------------
* Chỉ số *Lời khen (chu kỳ này)* và bảng *Người được ghi nhận nhiều nhất* trong khoảng thời gian của chu kỳ.
* Trang *Bảng xếp hạng*: bảng **Được ghi nhận nhiều nhất** (số lời khen *công khai* nhận được trong chu kỳ,
  theo công ty của người xem; dòng phụ là giá trị cốt lõi được ghi nhận nhiều nhất của người đó).
* *Không gian OKR* cá nhân: ô **Lời khen nhận được (tháng này)** mở bảng ghi nhận lọc theo lời khen của tôi.

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
*Cài đặt > OKR* (hoặc *OKR > Cấu hình > Cài đặt*): khối ứng dụng OKR trong Cài đặt do phân hệ này tạo ra
(``<app name="okr_scale">``), các phân hệ khác (ví dụ ``okr_scale_reward``) thêm khối cài đặt của mình vào đó.

* *Cho phép phản hồi ẩn danh*: mặc định **tắt** (nguyên tắc minh bạch của OKR).

*OKR > Cấu hình > Giá trị cốt lõi*: 5 giá trị mặc định (Khách hàng là trên hết, Tinh thần làm chủ,
Tinh thần đồng đội, Đổi mới sáng tạo, Chính trực) có thể chỉnh sửa.

Tác giả
=======
DMAG - Giấy phép LGPL-3

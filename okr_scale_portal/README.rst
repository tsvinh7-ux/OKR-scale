===========================
OKR Scale - Cổng khách hàng
===========================

Mở OKR cho tài khoản cổng thông tin (portal) để khách hàng B2B của DMAG cùng
theo dõi, cập nhật tiến độ và trao đổi về các mục tiêu chung, **có phân quyền**.

Tính năng
=========

* Trên mục tiêu (tab **Cổng khách hàng**, dành cho quản lý OKR):

  * **Khách hàng**: pháp nhân (công ty) được chia sẻ mục tiêu.
  * **Chia sẻ lên cổng khách hàng**: bật/tắt việc hiển thị trên cổng.
  * **Quyền trên cổng**: *Chỉ xem* hoặc *Xem và cập nhật tiến độ*.
  * Nút **Xem trên cổng KH** để xem trước giao diện khách hàng.

* Kết quả then chốt có thể giao cho tài khoản cổng của đúng khách hàng đó
  (ràng buộc kiểm tra: mục tiêu đã chia sẻ và người phụ trách thuộc công ty khách hàng).
* Cổng thông tin:

  * Thẻ **OKR** trên trang ``/my`` (đếm số mục tiêu được chia sẻ).
  * ``/my/okrs``: danh sách có phân trang, sắp xếp (mới nhất, tên, tiến độ),
    lọc theo trạng thái (đang triển khai / đã đóng) và theo chu kỳ.
  * ``/my/okr/<id>``: chi tiết mục tiêu, bảng kết quả then chốt, form cập nhật
    tiến độ (chỉ cho người phụ trách KR khi quyền là *Xem và cập nhật tiến độ*),
    lịch sử cập nhật gần đây và khung **Trao đổi** (chatter) giữa khách hàng và DMAG.

* Nhắc việc: khi quá hạn cập nhật, người phụ trách là tài khoản cổng nhận
  **email** (mẫu *OKR: nhắc cập nhật tiến độ (cổng khách hàng)*) có liên kết tới
  ``/my/okr/<id>``, tối đa một lần cho mỗi chu kỳ cập nhật (tuần / 2 tuần / tháng).
* Phía nội bộ: bộ lọc **Đã chia sẻ với khách hàng** và nhóm theo **Khách hàng**.

Phân quyền
==========

* Tài khoản cổng (``base.group_portal``) chỉ có quyền **đọc** mục tiêu, kết quả
  then chốt, cập nhật tiến độ, chu kỳ và thẻ; không có quyền ghi/tạo/xoá qua ORM.
* Quy tắc bản ghi: chỉ thấy mục tiêu **đã chia sẻ**, đang triển khai hoặc đã đóng,
  của **chính công ty mình** (``partner_id child_of`` công ty của người dùng)
  hoặc có KR do mình phụ trách. Không bao giờ thấy mục tiêu chưa chia sẻ, bản nháp
  hay mục tiêu của khách hàng khác.
* Cập nhật tiến độ đi qua controller ``POST /my/okr/kr/<id>/checkin`` (có CSRF):
  kiểm tra người dùng là tài khoản cổng, là người phụ trách KR, mục tiêu đang
  triển khai, đã chia sẻ và quyền là *Xem và cập nhật tiến độ*; dữ liệu được kiểm
  tra (số hợp lệ, mức tự tin 1-10, ghi chú tối đa 2000 ký tự) rồi mới ghi bằng sudo.
* Trường nội bộ (tự đánh giá, bài học kinh nghiệm, phản hồi của quản lý) chỉ dành
  cho người dùng nội bộ.
* Liên kết có mã truy cập (access token) **không** thay thế việc đăng nhập; mã bị
  huỷ khi bỏ chia sẻ hoặc đổi khách hàng.
* Người dùng nội bộ không bị ảnh hưởng bởi các quy tắc trên.

Cấu hình
========

#. Tạo tài khoản cổng cho liên hệ của khách hàng (Liên hệ > Hành động > Cấp quyền truy cập cổng).
#. Trên mục tiêu, tab **Cổng khách hàng**: chọn khách hàng, bật chia sẻ, chọn quyền.
#. Giao kết quả then chốt cho tài khoản cổng nếu khách hàng cần tự cập nhật tiến độ.

Tác giả
=======

DMAG

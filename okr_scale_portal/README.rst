===========================
OKR Scale - Cổng khách hàng
===========================

Chia sẻ OKR với từng liên hệ của khách hàng B2B trên cổng thông tin (portal),
**giống cơ chế cộng tác viên của Dự án (Project)**: mỗi người được mời có quyền
*Chỉ xem* hoặc *Cập nhật*. Giao diện cổng mang nhận diện thương hiệu DMAG.

Tính năng
=========

Phía nội bộ (backend)
---------------------

* Nút **Chia sẻ** trên đầu form mục tiêu (người phụ trách mục tiêu, quản lý của
  phòng ban / nhân viên và quản trị OKR) mở trình hướng dẫn chia sẻ:

  * chọn liên hệ cần mời, quyền **Chỉ xem** hoặc **Cập nhật**, lời nhắn tuỳ chọn;
  * **Gửi lời mời**: bật *Đã chia sẻ trên cổng*, tạo / cập nhật cộng tác viên,
    tự tạo **tài khoản cổng** cho liên hệ chưa có người dùng (giống trình
    *Cấp quyền truy cập cổng* chuẩn của Odoo) và gửi email mời có liên kết tới
    ``/my/okr/<id>`` (người dùng mới nhận liên kết đăng ký để đặt mật khẩu);
  * người được mời tự động theo dõi (follower) mục tiêu.

* Tab **Cổng khách hàng**: *Khách hàng* (thông tin, dùng để nhóm/báo cáo),
  *Đã chia sẻ trên cổng* (bật/tắt), danh sách **Cộng tác viên** có thể sửa quyền
  hoặc xoá.
* Nút thống kê **Cộng tác viên** và **Xem trên cổng KH**.
* Danh sách / tìm kiếm: bộ lọc **Đã chia sẻ với khách hàng**, nhóm theo
  **Khách hàng**, tìm theo cộng tác viên, cột số cộng tác viên.
* Kết quả then chốt có thể giao cho tài khoản cổng là cộng tác viên của mục tiêu;
  khi giao, người đó **tự động trở thành cộng tác viên có quyền Cập nhật**.

Cổng khách hàng
---------------

* Thẻ **OKR** (biểu tượng DMAG) trên trang ``/my``.
* ``/my/okrs`` - **OKR được chia sẻ**: phần đầu gradient DMAG, bộ lọc dạng nút
  (tất cả / đang triển khai / đã đóng, kèm số lượng), lọc theo chu kỳ, sắp xếp;
  mỗi mục tiêu là một thẻ: tên, chu kỳ, người phụ trách, vòng tiến độ, trạng thái,
  quyền truy cập (*Chỉ xem* / *Có thể cập nhật*), số kết quả then chốt.
* ``/my/okr/<id>``: phần đầu với vòng tiến độ lớn, chu kỳ, trạng thái, quyền,
  người phụ trách, các chỉ số (số KR, thời gian đã qua, mức tự tin, lần cập nhật
  gần nhất); danh sách kết quả then chốt với thanh tiến độ, mức tự tin, ngày cập
  nhật; **form cập nhật tiến độ** mở ngay dưới KR (ô nhập lớn, chọn mức tự tin 1-10
  dạng nút, gợi ý nội dung); dòng thời gian **cập nhật gần đây**; khung **Trao đổi**.
* Giao diện đáp ứng (1 cột trên điện thoại, 2-3 cột trên máy tính), tiếng Việt đầy đủ.

Nhắc việc
---------

Khi quá hạn cập nhật, người phụ trách KR là tài khoản cổng nhận **email**
(mẫu *OKR: portal check-in reminder*) có liên kết tới ``/my/okr/<id>``, tối đa
một lần cho mỗi chu kỳ cập nhật.

Phân quyền
==========

* Mô hình ``okr.scale.objective.collaborator``: mục tiêu, liên hệ, quyền
  (``read`` / ``edit``), duy nhất theo (mục tiêu, liên hệ). Nhân viên nội bộ không
  thể là cộng tác viên. Chỉ người có quyền chia sẻ mục tiêu mới tạo / sửa / xoá
  cộng tác viên. Không thể xoá hoặc hạ quyền một cộng tác viên đang phụ trách KR.
* Tài khoản cổng (``base.group_portal``) chỉ có quyền **đọc** qua ORM. Quy tắc bản
  ghi: thấy mục tiêu khi **đã chia sẻ**, **đang triển khai hoặc đã đóng**, và
  (là **cộng tác viên** của mục tiêu **hoặc** phụ trách một KR của mục tiêu).
  KR, cập nhật tiến độ (trừ bản nháp) và chu kỳ đi theo mục tiêu.
* **Không còn chia sẻ toàn công ty**: một liên hệ khác của cùng khách hàng không
  thấy gì cho tới khi được mời.
* Quyền **Cập nhật**: cập nhật tiến độ **mọi** KR của mục tiêu, bình luận, đính
  kèm tệp. Quyền **Chỉ xem**: xem và bình luận (không có form cập nhật, không đính
  kèm tệp - kiểm tra cả phía máy chủ tại ``/portal/attachment/add``).
* Cập nhật tiến độ đi qua ``POST /my/okr/kr/<id>/checkin`` (CSRF): kiểm tra tài
  khoản cổng, cộng tác viên quyền Cập nhật, mục tiêu đang triển khai và quy tắc
  bản ghi; dữ liệu được kiểm tra (số hợp lệ, mức tự tin 1-10, tối đa 2000 ký tự)
  rồi mới ghi bằng sudo.
* Trường nội bộ (tự đánh giá, bài học kinh nghiệm, phản hồi của quản lý) chỉ dành
  cho người dùng nội bộ. Liên kết có mã truy cập (access token) không thay thế đăng
  nhập; mã bị huỷ khi bỏ chia sẻ.
* Người dùng nội bộ không bị ảnh hưởng bởi các quy tắc trên.

Sử dụng
=======

#. Mở mục tiêu, bấm **Chia sẻ**, chọn liên hệ khách hàng và quyền, bấm **Gửi lời mời**.
#. Khi mục tiêu được duyệt (đang triển khai), khách hàng thấy mục tiêu trong ``/my/okrs``.
#. Đổi quyền hoặc xoá cộng tác viên trong tab **Cổng khách hàng**; tắt
   *Đã chia sẻ trên cổng* để ẩn mục tiêu với mọi cộng tác viên.

Tác giả
=======

DMAG

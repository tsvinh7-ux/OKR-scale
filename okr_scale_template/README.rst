============================
OKR Scale - Thư viện mẫu OKR
============================

Thư viện mẫu OKR dành cho chuỗi phòng khám nha khoa DMAG
("Nền tảng vận hành & tăng trưởng nha khoa"). Người dùng chọn một mẫu,
điều chỉnh chỉ tiêu cho phù hợp và có ngay một mục tiêu nháp với đầy đủ
kết quả then chốt (KR) chỉ trong một phút.

Tính năng
=========

* **Danh mục mẫu** có biểu tượng và màu riêng: Kinh doanh, Chăm sóc khách hàng,
  Lâm sàng / Chuyên môn, Marketing, Vận hành phòng khám, Nhân sự & Đào tạo,
  Tài chính, Công nghệ & Chuyển đổi số.
* **25 mẫu OKR** viết theo thông lệ tốt: mục tiêu định tính, truyền cảm hứng và
  3 - 4 KR đo lường được với chỉ số thực tế của phòng khám nha khoa (bệnh nhân
  mới, tỷ lệ chấp nhận kế hoạch điều trị, doanh thu/ghế, tỷ lệ vắng hẹn, NPS,
  điểm Google, tỷ lệ tái khám, ca implant/chỉnh nha, công suất ghế, thời gian
  chờ, audit vô khuẩn, CPL/CAC, giờ đào tạo, tỷ lệ nghỉ việc, AR days, hồ sơ
  bệnh án điện tử...). Mỗi KR có hướng dẫn **"Cách đo lường"**.
* **Nội dung song ngữ Anh - Việt** theo chuẩn Odoo: văn bản gốc của danh mục,
  mẫu, mô tả, từ khóa, KR, đơn vị và hướng dẫn đo lường viết bằng tiếng Anh;
  bản tiếng Việt nằm trong ``i18n/vi.po``. Người dùng thấy thư viện theo ngôn
  ngữ của mình (Tiếng Việt hoặc English), kể cả các KR được đề xuất trong
  trình hướng dẫn **Dùng mẫu**.
* **Thư viện dạng thẻ** (OKR > OKRs > Thư viện mẫu): bảng lọc theo danh mục kèm
  biểu tượng và số lượng, thẻ hiển thị danh mục, cấp đề xuất, tiêu đề mục
  tiêu, 3 KR đầu tiên, số lượt dùng và nút **Dùng mẫu**.
* **Dùng mẫu**: trình hướng dẫn chọn chu kỳ (mặc định chu kỳ hiện tại), cấp độ,
  nhân viên / phòng ban, **người chịu trách nhiệm chính**, **người hỗ trợ** và
  **phòng ban hỗ trợ** của mục tiêu, KR cấp trên để căn chỉnh và chỉnh trực
  tiếp giá trị ban đầu / mục tiêu / trọng số của từng KR (bỏ chọn KR không phù
  hợp). Mỗi KR có thể gán thêm **người hỗ trợ** riêng (cột tùy chọn "Người hỗ
  trợ" trong bảng KR). Hệ thống tạo **mục tiêu nháp** bằng chính quyền của người dùng
  (tuân thủ phân quyền theo cấp của OKR Scale) rồi mở mục tiêu đó.
* **Bắt đầu từ mẫu**: nút trên mục tiêu nháp chưa có KR để bổ sung KR từ mẫu.
  Người hỗ trợ / phòng ban hỗ trợ chọn trong trình hướng dẫn được **gộp thêm**
  vào danh sách sẵn có của mục tiêu (không xóa người đã có).
  Nút **Từ mẫu** trên danh sách mục tiêu.
* **Lưu thành mẫu** (quản lý OKR): biến một mục tiêu hiện có cùng các KR thành
  mẫu để chia sẻ cách làm hay giữa các chi nhánh.

Phân quyền
==========

* Người dùng OKR: xem thư viện và dùng mẫu.
* Quản lý OKR: tạo, sửa, lưu trữ mẫu; lưu mục tiêu thành mẫu.
* Quản trị OKR: thêm quản lý danh mục mẫu (Cấu hình > Danh mục mẫu).

Cách dùng
=========

#. Vào **OKR > OKRs > Thư viện mẫu**, chọn danh mục ở bảng bên trái.
#. Bấm **Dùng mẫu** trên thẻ phù hợp.
#. Kiểm tra cấp độ, người chịu trách nhiệm chính, người hỗ trợ, KR cấp trên;
   điều chỉnh chỉ tiêu.
#. Bấm **Tạo mục tiêu nháp**, hoàn thiện rồi **Gửi duyệt** như thường lệ.

Ghi chú
=======

* Dữ liệu mẫu được nạp với ``noupdate``: chỉnh sửa của bạn được giữ nguyên khi
  nâng cấp mô-đun.
* Cơ sở dữ liệu cài từ phiên bản 17.0.1.0.0 (nội dung mẫu gốc bằng tiếng Việt):
  khi nâng cấp, các bản ghi ``noupdate`` không bị ghi đè nên nội dung cũ được
  giữ nguyên (không bị nhân đôi KR nhờ script di chuyển gắn XML id cho các KR
  sẵn có). Muốn có nội dung song ngữ, cài mới mô-đun hoặc xóa / tạo lại các
  mẫu gốc.
* Để thêm ngôn ngữ khác, dịch tệp ``i18n/okr_scale_template.pot``.
* KR có giá trị mục tiêu nhỏ hơn giá trị ban đầu được hiểu là "càng thấp càng
  tốt" (ví dụ tỷ lệ vắng hẹn, thời gian chờ).

Tác giả
=======

DMAG - Giấy phép LGPL-3.

========================
OKR Scale - Cycle Review
========================

Phân hệ **Đánh giá chu kỳ** bổ sung cho phân hệ lõi ``okr_scale`` buổi **đánh giá giữa chu kỳ**
và buổi **nhìn lại cuối chu kỳ** (retrospective): một màn hình nhìn lại toàn bộ chu kỳ - điểm trung bình
theo từng cấp, điều làm tốt, bài học kinh nghiệm - và chuyển các KR chưa hoàn thành sang chu kỳ sau.

Thang điểm
==========

Theo thực hành OKR của Google (và các công cụ Microsoft Viva Goals, Perdoo, Weekdone, Lattice):

* Điểm từ **0.0 đến 1.0**, chia 3 dải màu: **đỏ** < 0.4 (chệch hướng), **vàng** 0.4 - 0.69
  (có tiến triển), **xanh** >= 0.7 (đạt).
* Mục tiêu **thách thức** (aspirational): 0.7 là "điểm ngọt"; luôn đạt 1.0 nghĩa là đặt mục tiêu quá thấp.
* Mục tiêu **cam kết** (committed): kỳ vọng đạt 1.0, mọi kết quả thấp hơn cần được giải thích.
* Điểm của một mục tiêu:

  - mục tiêu đã đóng: **điểm chốt** (``final_score``);
  - mục tiêu đang chạy, sau khi chu kỳ kết thúc: tiến độ / 100;
  - mục tiêu đang chạy, **trong chu kỳ**: **điểm dự phóng** = tiến độ ÷ thời gian đã qua (tối đa 1.0),
    tức điểm mục tiêu sẽ đạt nếu giữ nhịp hiện tại. 25 % đầu chu kỳ, thời gian dùng để dự phóng
    được tính tối thiểu 25 % để tránh kết luận vội.

Màn hình "Đánh giá chu kỳ"
==========================

Menu *OKR > Báo cáo > Đánh giá chu kỳ* (quản lý OKR) hoặc nút **Cycle Review** trên biểu mẫu chu kỳ.
Bộ lọc: chu kỳ, phòng ban (bao gồm phòng ban con). Số liệu được đọc theo quyền của người xem.

* **Banner**: tên chu kỳ, giai đoạn (giữa chu kỳ / nhìn lại cuối chu kỳ, theo ngày), vòng thời gian đã qua,
  số ngày còn lại, nút **Bắt đầu buổi đánh giá**.
* **Điểm tổng**: đồng hồ 0.0 - 1.0 theo dải màu, kết luận một câu ("Đạt một phần", "Đang hướng tới
  một chu kỳ tuyệt vời"...) và thanh thang điểm có vạch 0.4 / 0.7 / 1.0.
* **Chỉ số**: số mục tiêu (đã chấm), tiến độ trung bình so với thời gian đã qua, % đúng tiến độ,
  KR đã đạt, kỷ luật check-in (tỷ lệ check-in đã nộp so với kỳ vọng), số mục tiêu trong vùng đỏ.
* **Điểm theo cấp** (công ty / phòng ban / cá nhân): điểm trung bình, điểm chốt, tiến độ và thanh phân bố
  đỏ / vàng / xanh.
* **Cam kết và thách thức**: điểm trung bình so với chỉ tiêu (1.0 / 0.7), số mục tiêu đạt chỉ tiêu, lời khuyên.
* **Toàn cảnh phòng ban** (bản đồ nhiệt): điểm, tiến độ (trong chu kỳ: so với thời gian đã qua),
  % đúng tiến độ, kỷ luật check-in - mỗi ô tô màu theo dải.
* **Điểm sáng** (top 5) và **Vấn đề cần xử lý** (5 điểm thấp nhất dưới 0.7).
* **Các đội đã học được gì**: tường trích dẫn phần tự đánh giá và bài học kinh nghiệm của các mục tiêu.
* **Chuyển tiếp KR chưa hoàn thành**: danh sách có ô chọn, nút **Chuyển sang chu kỳ sau** mở trình hướng dẫn.
* **Các buổi đánh giá** của chu kỳ.

Buổi đánh giá (``okr.scale.review``)
====================================

Menu *OKR > OKRs > Đánh giá*. Mỗi buổi gồm: chu kỳ, loại (giữa chu kỳ / cuối chu kỳ), phòng ban
(để trống = toàn công ty), ngày, người điều phối, người tham gia, và 4 phần nội dung:
**Điều làm tốt**, **Điều cần cải thiện**, **Bài học kinh nghiệm**, **Quyết định & hành động tiếp theo**.

* Khi bắt đầu từ màn hình đánh giá, các phần được điền sẵn: mục tiêu đạt điểm ngọt, mục tiêu cần xử lý,
  bài học kinh nghiệm ghi trên các mục tiêu.
* **Ảnh chụp số liệu** (số mục tiêu, KR đạt, tiến độ, điểm trung bình, số lượng theo tình trạng
  và theo dải màu) được cập nhật khi đang thực hiện và **được chốt** khi *Kết thúc đánh giá*.
* Có chatter, hoạt động và người theo dõi.

Phân quyền
----------

* Người dùng OKR: **xem** các buổi đánh giá toàn công ty, của phòng ban mình, của phòng ban mình quản lý
  và các buổi mình điều phối / tham gia.
* Quản lý OKR: tạo / sửa / xoá buổi đánh giá cho **các phòng ban mình quản lý** (theo cây quản lý của
  ứng dụng Nhân viên - trường ``okr_manager_user_ids`` của phòng ban).
* Quản trị OKR: toàn quyền, kể cả buổi đánh giá toàn công ty.
* Quy tắc đa công ty theo công ty của chu kỳ.

Chuyển tiếp sang chu kỳ sau
===========================

Trình hướng dẫn *Chuyển KR sang chu kỳ tiếp theo* (``okr.scale.carry.over``):

* Chu kỳ đích bắt buộc, mặc định là chu kỳ kế tiếp theo ngày (ưu tiên cùng loại, cùng công ty, chưa đóng).
* Với mỗi mục tiêu có KR được chọn, một bản sao được tạo **một lần** trong chu kỳ đích ở trạng thái **nháp**
  (cùng cấp, người phụ trách, nhân viên, phòng ban, loại, phạm vi hiển thị, thẻ; liên kết căn chỉnh được giữ
  nếu KR cấp trên cũng đã được chuyển tiếp).
* Mỗi KR được chọn được sao chép với **khởi điểm = giá trị hiện tại** của chu kỳ trước, chỉ tiêu giữ nguyên,
  giá trị hiện tại = khởi điểm.
* Trường ``carried_from_id`` trên mục tiêu và KR liên kết với bản gốc; ghi chú được đăng trên cả hai phía.
* Thực hiện với quyền của người dùng: quản trị viên, quản lý của phòng ban / nhân viên, hoặc chính người
  phụ trách mục tiêu cá nhân. Một KR chỉ được chuyển tiếp một lần.

Nhắc việc tự động
=================

Tác vụ định kỳ *OKR: nhắc đánh giá chu kỳ* (hằng ngày):

* Khi chu kỳ đang chạy qua **50 %** thời gian: lên lịch hoạt động **Đánh giá giữa chu kỳ** trên chu kỳ cho
  quản trị viên OKR và quản lý các phòng ban có mục tiêu trong chu kỳ (một lần, cờ ``mid_review_reminded``).
* Khi chu kỳ kết thúc (hoặc được đóng): hoạt động **Đánh giá cuối chu kỳ** (một lần, cờ
  ``final_review_reminded``). Các chu kỳ đã kết thúc quá 14 ngày không được nhắc.

Kỹ thuật
========

* Nguồn dữ liệu: ``okr.scale.review.board.get_cycle_review_data(cycle_id, department_id)``.
* Giao diện OWL ``okr_scale_review.cycle_review`` dùng lại các thành phần ``OkrProgressRing``,
  ``OkrAvatar``, ``OkrStatusChip`` và bộ nhận diện DMAG của ``okr_scale``.
* Kiểm thử: ``--test-tags /okr_scale_review``.

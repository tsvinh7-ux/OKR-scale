===================
OKR Scale - Project
===================

Liên kết Kết quả then chốt (Key Result) của OKR với Dự án và Nhiệm vụ để tiến độ
Kết quả then chốt được cập nhật tự động theo tiến độ thực hiện nhiệm vụ.

Tính năng
=========

* Hai phương pháp đo lường mới cho Kết quả then chốt (trường *Đo lường theo*):

  * **Nhiệm vụ đã hoàn thành**: tiến độ = số nhiệm vụ đã hoàn thành / số nhiệm vụ
    không bị hủy.
  * **Nhiệm vụ đã hoàn thành (theo trọng số giờ được phân bổ)**: tiến độ = tổng giờ
    phân bổ của nhiệm vụ đã hoàn thành / tổng giờ phân bổ của nhiệm vụ không bị hủy.
    Nếu chưa có nhiệm vụ nào được phân bổ giờ, tiến độ được tính theo số lượng.

* Nhiệm vụ được tính cho một Kết quả then chốt gồm:

  * các nhiệm vụ liên kết trực tiếp qua trường *Kết quả then chốt* trên nhiệm vụ;
  * toàn bộ nhiệm vụ đang hoạt động (kể cả nhiệm vụ con) của các *Dự án* được liên
    kết với Kết quả then chốt.

  Mỗi nhiệm vụ chỉ được tính một lần. Nhiệm vụ đã lưu trữ và nhiệm vụ ở trạng thái
  *Đã hủy* bị loại trừ; nhiệm vụ ở trạng thái *Hoàn thành* được coi là đã xong.

* Tiến độ được tính lại ngay khi nhiệm vụ thay đổi trạng thái, giờ phân bổ, được
  thêm, lưu trữ hoặc liên kết; tiến độ Mục tiêu và các Kết quả then chốt cấp trên
  được cập nhật theo.
* Biểu mẫu Kết quả then chốt: tab **Dự án & Nhiệm vụ**, số nhiệm vụ hoàn thành / tổng
  số và nút thống kê mở danh sách nhiệm vụ.
* Nhiệm vụ: trường *Kết quả then chốt* trên biểu mẫu, cột tùy chọn trong danh sách,
  bộ lọc *Đã liên kết OKR* và nhóm theo Kết quả then chốt / Mục tiêu. Khi một nhiệm
  vụ liên kết trực tiếp được hoàn thành, một ghi chú ngắn được ghi vào Kết quả then
  chốt.
* Dự án: nút thông minh **OKR** hiển thị các Kết quả then chốt liên kết.
* Bảng điều khiển OKR: chỉ số **Nhiệm vụ liên kết đã hoàn thành** (% nhiệm vụ đã
  hoàn thành trên các Kết quả then chốt đang hiển thị).

Cấu hình và sử dụng
===================

1. Cài đặt module ``okr_scale_project`` (phụ thuộc ``okr_scale`` và ``project``).
2. Mở một Kết quả then chốt, chọn *Đo lường theo* = *Nhiệm vụ đã hoàn thành* hoặc
   *Nhiệm vụ đã hoàn thành (theo trọng số giờ được phân bổ)*.
3. Trong tab **Dự án & Nhiệm vụ**, chọn các dự án cần theo dõi; hoặc mở từng nhiệm
   vụ và chọn Kết quả then chốt tương ứng (chỉ các Kết quả then chốt của mục tiêu ở
   trạng thái Nháp, Chờ duyệt hoặc Đang thực hiện).

Phân quyền
==========

* Không có mô hình mới; quyền truy cập dự án và nhiệm vụ tuân theo quy tắc của module
  Dự án, quyền truy cập Kết quả then chốt tuân theo quy tắc của OKR Scale.
* Tiến độ được tính với quyền hệ thống nên luôn nhất quán, kể cả khi người hoàn thành
  nhiệm vụ không được xem Kết quả then chốt.
* Người dùng dự án vẫn thấy tên Kết quả then chốt được liên kết trên nhiệm vụ (hành vi
  chuẩn của trường Many2one trong Odoo), kể cả khi Mục tiêu ở chế độ riêng tư.

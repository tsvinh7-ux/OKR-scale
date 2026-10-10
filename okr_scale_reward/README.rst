===========================
OKR Scale - Rewards & Store
===========================

Phân hệ **Điểm thưởng & Cửa hàng quà tặng** cho ``okr_scale``: nhân viên tích điểm thưởng nhờ lời khen
của đồng nghiệp và kết quả OKR, sau đó đổi điểm lấy quà. Điểm thưởng **không phải tiền**, chỉ dùng để đổi quà.

Tính năng
=========

Sổ điểm (ledger) bất biến
-------------------------
* Mỗi biến động điểm là một giao dịch: lời khen, check-in, hoàn thành KR, hoàn thành mục tiêu,
  thủ công, đổi quà, hoàn điểm.
* Không ai (kể cả mã chạy với ``sudo``) sửa / xoá được giao dịch, trừ chính superuser; muốn điều chỉnh thì
  tạo một giao dịch điều chỉnh mới (*Cộng điểm* cho phép nhập số âm).
* Số dư ví, điểm đã tặng trong tháng và hạn mức còn lại là các trường tính toán trên người dùng
  (chỉ chính người dùng và quản trị OKR xem được).

Tặng điểm kèm lời khen
----------------------
* Trường *Điểm* trên lời khen (điểm cho **mỗi** người nhận).
* Kiểm tra: điểm >= 0, không vượt *Điểm tối đa mỗi lời khen*, tổng (điểm x số người nhận) không vượt
  phần còn lại của *Hạn mức tặng điểm hàng tháng* (tính theo các lời khen đã gửi trong tháng).
* Hạn mức tặng tách biệt với ví: tặng điểm không trừ ví của người tặng.
* Sau khi gửi không thể đổi điểm / người nhận; lời khen có điểm chỉ quản trị OKR xoá được
  (tự động tạo giao dịch điều chỉnh).

Điểm thưởng tự động từ OKR
--------------------------
* **Check-in**: cộng điểm cho người gửi check-in, tối đa một lần cho mỗi KR trong mỗi kỳ check-in của
  chu kỳ (``cycle.get_checkin_days()``), tính theo ngày gửi thực tế nên không thể "cày" điểm.
* **KR hoàn thành**: cộng một lần cho người phụ trách KR khi KR đạt mục tiêu lần đầu (kể cả KR đo từ
  các mục tiêu liên kết). KR được thêm sau khi mục tiêu đã được duyệt không được tính.
* **Mục tiêu thành công**: cộng một lần cho người phụ trách khi mục tiêu được đóng với điểm cuối kỳ >= 0.7.

Cửa hàng quà tặng
-----------------
* Quà tặng: hình ảnh, giá (điểm), danh mục, giới hạn số lượng, sản phẩm liên kết (tuỳ chọn), công ty.
* Nút **Đổi quà** mở hộp thoại hiển thị số dư hiện tại và số dư sau khi đổi.
* Yêu cầu đổi quà (mã ``RDM/<năm>/xxxxx``): trừ điểm và giữ hàng ngay khi tạo; quản trị OKR
  được giao hoạt động để xử lý: Duyệt -> Đã trao, hoặc Từ chối. Từ chối / huỷ sẽ hoàn điểm và trả lại hàng.

Báo cáo
-------
* *Điểm của tôi* (tổng danh sách = số dư), *Quà đã đổi của tôi*.
* Cho quản trị OKR: tất cả yêu cầu đổi quà, giao dịch điểm, bảng xếp hạng (biểu đồ / pivot, mặc định tháng này).
* Bảng điều khiển OKR: chỉ số *Điểm thưởng đã cộng (chu kỳ này)* và bảng *Bảng xếp hạng* (top 10).

Cấu hình
========
*Cài đặt > OKR* (hoặc *OKR > Cấu hình > Điểm thưởng & Quà tặng > Cài đặt*):

=====================================  ===========
Tham số                                Mặc định
=====================================  ===========
Hạn mức tặng điểm hàng tháng           100
Điểm tối đa mỗi lời khen               50
Điểm cho mỗi check-in                  5
Điểm cho mỗi KR hoàn thành             50
Điểm cho mỗi mục tiêu thành công       100
=====================================  ===========

Đặt giá trị 0 để tắt loại điểm thưởng tương ứng.

Phân quyền
==========
* Giao dịch điểm: người dùng chỉ xem giao dịch của mình; quản trị OKR xem tất cả; không ai tạo trực tiếp
  (mã nguồn dùng ``sudo`` sau khi kiểm tra).
* Yêu cầu đổi quà: người dùng tạo / xem / huỷ yêu cầu của mình; quản trị OKR xử lý tất cả.
* Quà tặng: người dùng chỉ đọc; quản trị OKR quản lý.
* Quy tắc đa công ty cho giao dịch, quà tặng và yêu cầu đổi quà.

Tác giả
=======
DMAG - Giấy phép LGPL-3

============================
OKR Scale - Reward Inventory
============================

Phân hệ tuỳ chọn kết nối **Cửa hàng quà tặng** (``okr_scale_reward``) với ứng dụng **Tồn kho** (``stock``).
Công ty chưa cần mua sẵn quà vào kho: quà có thể được đổi trước (đặt trước) và được giao khi hàng về,
nhưng toàn bộ số lượng và việc xuất kho đều được quản lý đúng trong Tồn kho.

Tính năng
=========

Quà tặng quản lý trong tồn kho
------------------------------
* Ô **Quản lý trong tồn kho** trên quà tặng (*OKR > Cấu hình > Điểm thưởng > Quà tặng*).
* Nếu quà chưa có sản phẩm, hệ thống tự tạo một **sản phẩm lưu kho** (không bán, có thể mua) cùng tên,
  hình ảnh và công ty với quà tặng.
* Khi được quản lý trong tồn kho, bộ đếm thủ công *Giới hạn số lượng* bị tắt: số lượng khả dụng được đọc
  từ kho hàng của công ty (*Có thể sử dụng* = tồn kho chưa được giữ cho phiếu giao hàng nào), trừ đi số
  lượng của các yêu cầu đổi quà chưa được duyệt.
* Nút thống kê *Tồn kho* (cho người dùng Tồn kho) mở sản phẩm.

Đặt trước (pre-order)
---------------------
* Cài đặt **Cho phép đổi quà khi chưa có hàng (đặt trước)** trong *Cài đặt > OKR > Cửa hàng quà tặng*
  (tham số ``okr_scale_reward_stock.allow_preorder``), **mặc định bật** vì công ty chưa mua quà sẵn.
* Bật: nhân viên đổi được quà kể cả khi hết hàng, thẻ quà hiển thị nhãn *Đặt trước*; phiếu giao hàng chờ hàng về.
* Tắt: không đổi được khi số lượng khả dụng nhỏ hơn số lượng yêu cầu (thông báo "Chỉ còn N ...").

Quy trình giao quà
------------------
* **Duyệt** yêu cầu đổi quà -> tạo phiếu xuất kho (loại phiếu *Giao hàng* của kho công ty, đối tác là
  liên hệ công việc của nhân viên, hoặc đối tác của người dùng; *Chứng từ gốc* = mã yêu cầu ``RDM/...``),
  xác nhận và giữ hàng ngay nếu có.
* **Đánh dấu đã trao** trên yêu cầu -> xác nhận phiếu giao hàng (yêu cầu quà đã được giữ đủ trong kho,
  nếu chưa có hàng sẽ báo lỗi để nhập kho trước).
* Ngược lại, xác nhận phiếu giao hàng trong Tồn kho -> yêu cầu đổi quà tự động chuyển sang *Đã trao*.
* **Từ chối** hoặc **huỷ** yêu cầu -> phiếu giao hàng chưa hoàn tất bị huỷ (điểm được hoàn như trước).
* Phiếu giao hàng bị huỷ trong Tồn kho: nút **Tạo phiếu giao hàng** trên yêu cầu đã duyệt để tạo lại.
* Danh sách yêu cầu đổi quà có cột *Trạng thái giao hàng*; biểu mẫu có nút thống kê *Phiếu giao*.

Phân quyền
==========
* Phiếu kho và sản phẩm được tạo bằng ``sudo`` sau khi kiểm tra quyền *Quản trị OKR*: người duyệt quà không cần
  quyền Tồn kho. Số lượng tồn kho không nhạy cảm nên mọi người dùng OKR đều thấy tình trạng hàng của quà.
* Đa công ty: kho, phiếu giao hàng và sản phẩm theo công ty của yêu cầu đổi quà / quà tặng.

Tác giả
=======
DMAG - Giấy phép LGPL-3

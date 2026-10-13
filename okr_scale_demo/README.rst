==========================
OKR Scale - DMAG Demo Data
==========================

Bộ dữ liệu demo đầy đủ và sát thực tế cho bộ ứng dụng OKR của
**DMAG - Nền Tảng Vận Hành & Tăng Trưởng Nha Khoa**. Cài xong là mọi màn hình
(My OKR, check-in hằng tuần, dashboard, xếp hạng, cây OKR, CFR, cửa hàng quà,
đánh giá chu kỳ, thư viện mẫu, cổng khách hàng) đều có dữ liệu.

.. warning::
   Chỉ cài module này trên **cơ sở dữ liệu demo riêng**. Module đổi tên công ty
   thành DMAG, tạo người dùng, phòng ban và lưu trữ (archive) dữ liệu mẫu nhân sự
   / dự án của Odoo nếu có.

Cài đặt trên máy cá nhân
========================

.. code-block:: bash

   ./odoo-bin -c odoo.conf -d okr_demo -i okr_scale_demo --load-language=vi_VN --stop-after-init
   ./odoo-bin -c odoo.conf -d okr_demo

Mở http://localhost:8069. Dữ liệu được tạo một lần bởi ``post_init_hook``
(tham số hệ thống ``okr_scale_demo.loaded`` đánh dấu đã tạo, chạy lại không tạo trùng).
Ngày tháng (check-in, check-in tuần, lời khen, 1:1...) được tính theo **ngày cài đặt**.
Khuyến nghị dùng ``--without-demo=all`` khi tạo cơ sở dữ liệu mới để giao diện gọn hơn.

Tài khoản demo
==============

Mật khẩu của mọi tài khoản dưới đây: ``dmag2026`` (riêng ``admin`` giữ mật khẩu
đã chọn khi tạo cơ sở dữ liệu, thường là ``admin``).

========================== ============================ =====================================
Đăng nhập                  Họ tên                       Vai trò
========================== ============================ =====================================
``admin``                  Lê Minh Tuấn                 Phó TGĐ - OKR Champion, quản trị OKR
``ceo@dmag.vn``            Nguyễn Văn Hùng              Tổng Giám đốc, quản trị OKR
``kinhdoanh@dmag.vn``      Trần Thị Mai                 Giám đốc Kinh doanh (quản lý)
``nv.kinhdoanh1@dmag.vn``  Phạm Đức Anh                 Chuyên viên Phát triển Khách hàng
``nv.kinhdoanh2@dmag.vn``  Võ Thị Thu Hà                Chuyên viên Phát triển Khách hàng
``nv.kinhdoanh3@dmag.vn``  Đặng Minh Khoa               Account Manager
``cskh@dmag.vn``           Hoàng Thị Lan                Trưởng phòng CSKH (quản lý)
``nv.cskh1@dmag.vn``       Bùi Thanh Tâm                Chuyên viên Hỗ trợ Khách hàng
``nv.cskh2@dmag.vn``       Ngô Thị Hồng                 Chuyên viên Customer Success
``lamsang@dmag.vn``        BS. Lý Quốc Thịnh            Giám đốc Chuyên môn (quản lý)
``nv.lamsang1@dmag.vn``    BS. Trịnh Ngọc Hân           Bác sĩ Chỉnh nha - Đào tạo
``nv.lamsang2@dmag.vn``    Mai Văn Phúc                 Điều dưỡng trưởng
``marketing@dmag.vn``      Đỗ Thùy Linh                 Trưởng phòng Marketing (quản lý)
``nv.marketing1@dmag.vn``  Phan Gia Huy                 Performance Marketing
``nv.marketing2@dmag.vn``  Lâm Ngọc Trâm                Nội dung & Thương hiệu
``vanhanh@dmag.vn``        Vũ Đức Thắng                 Giám đốc Vận hành (quản lý)
``nv.vanhanh1@dmag.vn``    Cao Thị Yến                  Chuyên viên Triển khai Phòng khám
``nv.vanhanh2@dmag.vn``    Hồ Minh Nhật                 Kỹ sư Tích hợp Hệ thống
``nhansu@dmag.vn``         Trương Thị Ngọc              Trưởng phòng Nhân sự (quản lý)
``nv.nhansu1@dmag.vn``     Đinh Quang Vinh              Chuyên viên Tuyển dụng
``taichinh@dmag.vn``       Lương Văn Đạt                Kế toán trưởng (quản lý)
``nv.taichinh1@dmag.vn``   Kiều Thị Phương              Kế toán Công nợ
``anhduong.giamdoc@demo.vn`` Nguyễn Thị Ánh Dương       Cổng khách hàng - quyền chỉnh sửa
``anhduong.ketoan@demo.vn``  Phạm Văn Lộc               Cổng khách hàng - chỉ xem
========================== ============================ =====================================

Nội dung demo
=============

* **Công ty DMAG** có logo, 8 phòng ban (Ban Giám đốc và 7 phòng trực thuộc), 22 nhân viên
  gắn với người dùng, ảnh đại diện, chức danh, quản lý trực tiếp.
* **Chu kỳ**: Năm 2026 (đang chạy), Quý 3/2026 (đã đóng, đã chấm điểm, có tự đánh giá,
  bài học và buổi tổng kết cuối chu kỳ), Quý 4/2026 (chu kỳ hiện tại, check-in thứ Sáu 14:00),
  Quý 1/2027 (đang lập kế hoạch).
* **OKR quý 4**: 3 mục tiêu công ty x 3 KR, mục tiêu phòng ban căn chỉnh vào KR công ty
  (một số KR đo "từ các mục tiêu căn chỉnh"), mục tiêu cá nhân căn chỉnh vào KR phòng ban,
  cam kết / tham vọng, phòng ban và người hỗ trợ, một mục tiêu riêng tư, mục tiêu nháp và
  chờ duyệt.
* **Lịch sử**: check-in hằng tuần từ đầu quý (có KR vượt tiến độ, chậm, đứng yên, tự tin thấp
  kèm vướng mắc), check-in tuần (tóm tắt, kế hoạch, cần hỗ trợ), một số người chưa nộp tuần này.
* **Dự án** "Triển khai hệ thống đặt lịch online" (12 nhiệm vụ) gắn với KR đo theo nhiệm vụ.
* **CFR**: 16 lời khen theo giá trị cốt lõi kèm điểm thưởng, góp ý minh bạch, yêu cầu góp ý,
  các buổi 1:1 đã diễn ra (có ghi chú, buổi tiếp theo tự lên lịch) và các buổi 1:1 tuần này.
* **Phần thưởng**: điểm cho mọi người, 8 món quà có hình ảnh, các yêu cầu đổi quà ở nhiều trạng thái.
* **Cổng khách hàng**: Nha khoa Ánh Dương với mục tiêu chung "Tăng 30% bệnh nhân chỉnh nha
  tại Nha khoa Ánh Dương"; KR do giám đốc phòng khám phụ trách và check-in từ cổng (/my/okrs).
* **Thư viện mẫu**: 2 mục tiêu được tạo từ mẫu OKR.

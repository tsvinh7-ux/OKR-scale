"""Vietnamese content of the DMAG demo.

Everything the post-install hook creates is described here as plain data, so the
demo can be adjusted without touching the loading logic in ``hooks.py``.
"""

PASSWORD = 'dmag2026'

COMPANY = {
    'name': 'DMAG',
    'website': 'https://dmag.vn',
    'email': 'hello@dmag.vn',
    'phone': '+84 28 7300 2026',
    'street': '72 Lê Thánh Tôn, Phường Bến Nghé',
    'city': 'TP. Hồ Chí Minh',
    'company_registry': '0318 202 626',
}

# key, name, parent key, manager key
DEPARTMENTS = [
    ('bgd', 'Ban Giám đốc', None, 'ceo'),
    ('kd', 'Kinh doanh', 'bgd', 'kd_mgr'),
    ('cskh', 'Chăm sóc khách hàng', 'bgd', 'cskh_mgr'),
    ('ls', 'Lâm sàng', 'bgd', 'ls_mgr'),
    ('mkt', 'Marketing', 'bgd', 'mkt_mgr'),
    ('vh', 'Vận hành', 'bgd', 'vh_mgr'),
    ('ns', 'Nhân sự', 'bgd', 'ns_mgr'),
    ('tc', 'Tài chính', 'bgd', 'tc_mgr'),
]

# key, name, login (None = existing admin user), department, job title, manager key, phone
PEOPLE = [
    ('ceo', 'Nguyễn Văn Hùng', 'ceo@dmag.vn', 'bgd', 'Tổng Giám đốc (CEO)', None, '0903 100 001'),
    ('admin', 'Lê Minh Tuấn', None, 'bgd', 'Phó Tổng Giám đốc - OKR Champion', 'ceo', '0903 100 002'),
    ('kd_mgr', 'Trần Thị Mai', 'kinhdoanh@dmag.vn', 'kd', 'Giám đốc Kinh doanh', 'ceo', '0903 100 010'),
    ('kd1', 'Phạm Đức Anh', 'nv.kinhdoanh1@dmag.vn', 'kd', 'Chuyên viên Phát triển Khách hàng', 'kd_mgr', '0903 100 011'),
    ('kd2', 'Võ Thị Thu Hà', 'nv.kinhdoanh2@dmag.vn', 'kd', 'Chuyên viên Phát triển Khách hàng', 'kd_mgr', '0903 100 012'),
    ('kd3', 'Đặng Minh Khoa', 'nv.kinhdoanh3@dmag.vn', 'kd', 'Account Manager', 'kd_mgr', '0903 100 013'),
    ('cskh_mgr', 'Hoàng Thị Lan', 'cskh@dmag.vn', 'cskh', 'Trưởng phòng Chăm sóc Khách hàng', 'ceo', '0903 100 020'),
    ('cs1', 'Bùi Thanh Tâm', 'nv.cskh1@dmag.vn', 'cskh', 'Chuyên viên Hỗ trợ Khách hàng', 'cskh_mgr', '0903 100 021'),
    ('cs2', 'Ngô Thị Hồng', 'nv.cskh2@dmag.vn', 'cskh', 'Chuyên viên Customer Success', 'cskh_mgr', '0903 100 022'),
    ('ls_mgr', 'BS. Lý Quốc Thịnh', 'lamsang@dmag.vn', 'ls', 'Giám đốc Chuyên môn', 'ceo', '0903 100 030'),
    ('ls1', 'BS. Trịnh Ngọc Hân', 'nv.lamsang1@dmag.vn', 'ls', 'Bác sĩ Chỉnh nha - Đào tạo', 'ls_mgr', '0903 100 031'),
    ('ls2', 'Mai Văn Phúc', 'nv.lamsang2@dmag.vn', 'ls', 'Điều dưỡng trưởng - Kiểm soát nhiễm khuẩn', 'ls_mgr', '0903 100 032'),
    ('mkt_mgr', 'Đỗ Thùy Linh', 'marketing@dmag.vn', 'mkt', 'Trưởng phòng Marketing', 'ceo', '0903 100 040'),
    ('mk1', 'Phan Gia Huy', 'nv.marketing1@dmag.vn', 'mkt', 'Chuyên viên Performance Marketing', 'mkt_mgr', '0903 100 041'),
    ('mk2', 'Lâm Ngọc Trâm', 'nv.marketing2@dmag.vn', 'mkt', 'Chuyên viên Nội dung & Thương hiệu', 'mkt_mgr', '0903 100 042'),
    ('vh_mgr', 'Vũ Đức Thắng', 'vanhanh@dmag.vn', 'vh', 'Giám đốc Vận hành', 'admin', '0903 100 050'),
    ('vh1', 'Cao Thị Yến', 'nv.vanhanh1@dmag.vn', 'vh', 'Chuyên viên Triển khai Phòng khám', 'vh_mgr', '0903 100 051'),
    ('vh2', 'Hồ Minh Nhật', 'nv.vanhanh2@dmag.vn', 'vh', 'Kỹ sư Tích hợp Hệ thống', 'vh_mgr', '0903 100 052'),
    ('ns_mgr', 'Trương Thị Ngọc', 'nhansu@dmag.vn', 'ns', 'Trưởng phòng Nhân sự', 'admin', '0903 100 060'),
    ('ns1', 'Đinh Quang Vinh', 'nv.nhansu1@dmag.vn', 'ns', 'Chuyên viên Tuyển dụng', 'ns_mgr', '0903 100 061'),
    ('tc_mgr', 'Lương Văn Đạt', 'taichinh@dmag.vn', 'tc', 'Kế toán trưởng', 'ceo', '0903 100 070'),
    ('tc1', 'Kiều Thị Phương', 'nv.taichinh1@dmag.vn', 'tc', 'Chuyên viên Kế toán Công nợ', 'tc_mgr', '0903 100 071'),
]

PORTAL = {
    'company': 'Nha khoa Ánh Dương',
    'company_city': 'Biên Hòa, Đồng Nai',
    'company_street': '128 Phạm Văn Thuận, Tân Mai',
    'users': [
        # key, name, login, access mode, function
        ('pt_edit', 'Nguyễn Thị Ánh Dương', 'anhduong.giamdoc@demo.vn', 'edit', 'Giám đốc phòng khám'),
        ('pt_read', 'Phạm Văn Lộc', 'anhduong.ketoan@demo.vn', 'read', 'Kế toán trưởng'),
    ],
}

TAGS = [
    ('growth', 'Tăng trưởng', 10),
    ('customer', 'Khách hàng', 4),
    ('digital', 'Số hoá', 2),
    ('people', 'Con người', 7),
    ('quality', 'Chất lượng', 3),
]

CYCLES = [
    # key, name, type, start, end, state, parent
    ('y2026', 'Năm 2026', 'year', '2026-01-01', '2026-12-31', 'open', None),
    ('q3', 'Quý 3/2026', 'quarter', '2026-07-01', '2026-09-30', 'closed', 'y2026'),
    ('q4', 'Quý 4/2026', 'quarter', '2026-10-01', '2026-12-31', 'open', 'y2026'),
    ('q1', 'Quý 1/2027', 'quarter', '2027-01-01', '2027-03-31', 'draft', None),
]


def kr(key, name, start=0.0, target=100.0, unit='', owner=None, profile='on', metric='number',
       method='manual', blocker=None, contributors=(), final=None, weight=1.0):
    """Key result description. ``profile`` drives the generated check-in history:
    ahead / on / behind / blocked / stalled / none / done. ``final`` is the end value (closed cycles)."""
    if metric == 'percent' and not unit:
        unit = '%'
    if metric == 'boolean':
        start, target = 0.0, 1.0
    return {
        'key': key, 'name': name, 'start': float(start), 'target': float(target), 'unit': unit,
        'owner': owner, 'profile': profile, 'metric': metric, 'method': method, 'blocker': blocker,
        'contributors': list(contributors), 'final': final, 'weight': weight,
    }


def obj(key, name, level, krs, owner=None, dept=None, parent=None, okr_type='committed', visibility='public',
        state='running', tags=(), contributor_users=(), contributor_depts=(), description=None, **extra):
    values = {
        'key': key, 'name': name, 'level': level, 'krs': krs, 'owner': owner, 'dept': dept, 'parent': parent,
        'okr_type': okr_type, 'visibility': visibility, 'state': state, 'tags': list(tags),
        'contributor_users': list(contributor_users), 'contributor_depts': list(contributor_depts),
        'description': description,
    }
    values.update(extra)
    return values


# ----------------------------------------------------------------------
# Year 2026: monthly check-ins until the end of Q3
# ----------------------------------------------------------------------
YEAR_OBJECTIVES = [
    obj('y_lead', 'Trở thành nền tảng vận hành nha khoa được tin dùng nhất Việt Nam', 'company', [
        kr('y_clinics', '300 phòng khám đối tác đang hoạt động trên nền tảng DMAG', 180, 300, 'phòng khám',
           owner='ceo', final=251),
        kr('y_revenue', 'Doanh thu năm 2026 đạt 36 tỷ đồng', 0, 36, 'tỷ đồng', owner='ceo', final=25.4),
    ], owner='ceo', tags=['growth'], okr_type='aspirational',
        description='<p>Định hướng năm 2026 của DMAG: mở rộng mạng lưới phòng khám đối tác trên toàn quốc '
                    'và trở thành lựa chọn số một về phần mềm vận hành &amp; tăng trưởng cho nha khoa.</p>'),
    obj('y_org', 'Xây dựng tổ chức vận hành chuẩn mực, ra quyết định bằng dữ liệu', 'company', [
        kr('y_digital', 'Số hoá 100% quy trình cốt lõi', 20, 100, metric='percent', owner='admin', final=64),
        kr('y_enps', 'eNPS toàn công ty đạt 35 điểm', 10, 35, 'điểm', owner='admin', final=23),
    ], owner='admin', tags=['digital', 'people']),
]

# ----------------------------------------------------------------------
# Q3 2026: closed and graded cycle
# ----------------------------------------------------------------------
Q3_OBJECTIVES = [
    obj('q3_co1', 'Tăng tốc mở rộng mạng lưới phòng khám đối tác', 'company', [
        kr('q3_co1_k1', 'Ký mới 20 phòng khám đối tác', 0, 20, 'phòng khám', owner='kd_mgr', final=18),
        kr('q3_co1_k2', 'MRR đạt 2,4 tỷ đồng', 1.9, 2.4, 'tỷ đồng', owner='ceo', final=2.4),
    ], owner='ceo', tags=['growth'],
        self_assessment='Quý bám sát kế hoạch: MRR đạt mục tiêu, số phòng khám mới đạt 90%. '
                        'Hai hợp đồng chuỗi lớn trượt sang tháng 10.',
        lessons='Các chuỗi lớn cần chu kỳ bán hàng 8-10 tuần: phải đưa vào pipeline từ đầu quý.'),
    obj('q3_co2', 'Nâng cao mức độ hài lòng của phòng khám đối tác', 'company', [
        kr('q3_co2_k1', 'NPS đối tác đạt 50 điểm', 38, 50, 'điểm', owner='cskh_mgr', final=48),
        kr('q3_co2_k2', 'Thời gian phản hồi yêu cầu hỗ trợ dưới 6 giờ', 12, 6, 'giờ', owner='cskh_mgr', final=6.5),
    ], owner='ceo', tags=['customer'],
        self_assessment='NPS tăng 10 điểm nhờ quy trình hỗ trợ mới; thời gian phản hồi gần đạt mục tiêu.',
        lessons='Đo NPS hằng tháng thay vì cuối quý để phản ứng nhanh hơn.'),
    obj('q3_co3', 'Số hoá vận hành phòng khám đối tác', 'company', [
        kr('q3_co3_k1', 'Thí điểm đặt lịch online tại 20 phòng khám', 0, 20, 'phòng khám', owner='vh_mgr', final=12),
        kr('q3_co3_k2', 'Chuẩn hoá 20 quy trình SOP', 0, 20, 'quy trình', owner='admin', final=14),
    ], owner='admin', okr_type='aspirational', tags=['digital'],
        self_assessment='Mục tiêu tham vọng, đạt khoảng 65%: thí điểm đặt lịch chậm do tích hợp phần mềm cũ.',
        lessons='Khảo sát hạ tầng phần mềm của phòng khám trước khi cam kết lịch go-live.'),
    obj('q3_kd', 'Tăng tốc bán hàng khu vực TP.HCM', 'department', [
        kr('q3_kd_k1', 'Ký 20 hợp đồng phòng khám', 0, 20, 'hợp đồng', owner='kd_mgr', final=18),
        kr('q3_kd_k2', 'Thực hiện 80 buổi demo sản phẩm', 0, 80, 'buổi', owner='kd1', final=86),
    ], dept='kd', parent='q3_co1_k1', tags=['growth'],
        self_assessment='Số buổi demo vượt 8%, tỷ lệ chốt chưa đạt kỳ vọng ở nhóm phòng khám nhỏ.',
        lessons='Chuẩn bị gói trả góp cho phòng khám nhỏ ngay từ buổi demo đầu tiên.'),
    obj('q3_cskh', 'Chuẩn hoá quy trình hỗ trợ khách hàng', 'department', [
        kr('q3_cs_k1', 'Ban hành bộ kịch bản hỗ trợ chuẩn DMAG', metric='boolean', owner='cskh_mgr', final=1),
        kr('q3_cs_k2', 'Thời gian phản hồi dưới 6 giờ', 12, 6, 'giờ', owner='cs1', final=6.5),
    ], dept='cskh', parent='q3_co2_k2', tags=['customer'],
        self_assessment='Bộ kịch bản hỗ trợ đã áp dụng cho 100% ca trực.',
        lessons='Ca trực tối thứ Bảy cần thêm 1 người khi số phòng khám tăng.'),
    obj('q3_ls', 'Đào tạo lâm sàng cho bác sĩ đối tác', 'department', [
        kr('q3_ls_k1', 'Đào tạo 40 bác sĩ đối tác', 0, 40, 'bác sĩ', owner='ls1', final=41),
        kr('q3_ls_k2', 'Tỷ lệ tái khám đúng hẹn đạt 70%', 58, 70, metric='percent', owner='ls_mgr', final=63),
    ], dept='ls', parent='q3_co2_k1', tags=['quality'],
        self_assessment='Vượt chỉ tiêu đào tạo; tỷ lệ tái khám mới cải thiện 5 điểm.',
        lessons='Nhắc hẹn tự động qua Zalo hiệu quả hơn gọi điện thủ công.'),
    obj('q3_mkt', 'Ra mắt nhận diện thương hiệu DMAG mới', 'department', [
        kr('q3_mk_k1', 'Thu hút 300 lead phòng khám (MQL)', 0, 300, 'lead', owner='mk1', final=212),
        kr('q3_mk_k2', 'Ra mắt website dmag.vn phiên bản mới', metric='boolean', owner='mkt_mgr', final=1),
    ], dept='mkt', parent='q3_co1_k1', okr_type='aspirational', tags=['growth'],
        self_assessment='Website mới ra mắt đúng hạn; số lead đạt 70% do ngân sách quảng cáo tháng 8 bị cắt.',
        lessons='Cần thoả thuận ngân sách quảng cáo cố định theo quý với Tài chính.'),
    obj('q3_vh', 'Thí điểm đặt lịch online cho phòng khám đối tác', 'department', [
        kr('q3_vh_k1', 'Go-live đặt lịch online tại 20 phòng khám', 0, 20, 'phòng khám', owner='vh1', final=12),
        kr('q3_vh_k2', 'Thời gian onboarding phòng khám dưới 14 ngày', 21, 14, 'ngày', owner='vh_mgr', final=17),
    ], dept='vh', parent='q3_co3_k1', tags=['digital'],
        self_assessment='12/20 phòng khám go-live, onboarding còn 17 ngày. 8 phòng khám còn lại dùng phần mềm cũ không có API.',
        lessons='Chuyển 8 phòng khám chưa xong sang quý 4 và làm bộ chuyển đổi dữ liệu.'),
    obj('q3_ns', 'Hoàn thiện bộ máy nhân sự cho giai đoạn tăng trưởng', 'department', [
        kr('q3_ns_k1', 'Tuyển 8 vị trí theo kế hoạch', 0, 8, 'vị trí', owner='ns1', final=5),
        kr('q3_ns_k2', 'Ban hành khung năng lực cho 7 phòng ban', metric='boolean', owner='ns_mgr', final=1),
    ], dept='ns', parent='q3_co3_k2', tags=['people'],
        self_assessment='Khung năng lực hoàn tất; tuyển dụng vị trí kỹ thuật còn khó.',
        lessons='Mở kênh giới thiệu nội bộ có thưởng cho vị trí kỹ thuật.'),
    obj('q3_tc', 'Kiểm soát dòng tiền và công nợ', 'department', [
        kr('q3_tc_k1', 'Tỷ lệ công nợ quá hạn dưới 20%', 30, 20, metric='percent', owner='tc1', final=18),
        kr('q3_tc_k2', 'Gửi báo cáo quản trị trước ngày 10 hằng tháng', metric='boolean', owner='tc_mgr', final=1),
    ], dept='tc', parent='q3_co1_k2', tags=['growth'],
        self_assessment='Đạt cả hai kết quả then chốt, công nợ quá hạn giảm còn 18%.',
        lessons='Nhắc nợ tự động trước hạn 5 ngày giúp giảm mạnh công nợ quá hạn.'),
    obj('q3_i_kd1', 'Bứt phá doanh số cá nhân quý 3', 'individual', [
        kr('q3_i_kd1_k1', 'Ký 8 hợp đồng phòng khám', 0, 8, 'hợp đồng', final=9),
        kr('q3_i_kd1_k2', 'Thực hiện 35 buổi demo', 0, 35, 'buổi', final=33),
    ], owner='kd1', parent='q3_kd_k1',
        self_assessment='Vượt chỉ tiêu hợp đồng nhờ tập trung vào chuỗi 2-3 phòng khám.',
        lessons='Chuẩn bị case study theo từng quận giúp khách hàng tin tưởng hơn.'),
    obj('q3_i_cs1', 'Nâng chất lượng hỗ trợ khách hàng', 'individual', [
        kr('q3_i_cs1_k1', 'CSAT sau hỗ trợ đạt 4,5/5', 4.0, 4.5, 'điểm', final=4.4),
        kr('q3_i_cs1_k2', 'Viết 15 bài hướng dẫn trên trung tâm trợ giúp', 0, 15, 'bài', final=15),
    ], owner='cs1', parent='q3_cs_k2',
        self_assessment='Hoàn thành 15 bài hướng dẫn, CSAT tăng đều mỗi tháng.',
        lessons='Video ngắn 2 phút được lễ tân phòng khám xem nhiều hơn bài viết dài.'),
    obj('q3_i_mk1', 'Tối ưu chi phí quảng cáo B2B', 'individual', [
        kr('q3_i_mk1_k1', 'Chi phí mỗi lead dưới 600 nghìn đồng', 900, 600, 'nghìn đồng', final=720),
        kr('q3_i_mk1_k2', 'Thu 200 lead từ quảng cáo', 0, 200, 'lead', final=118),
    ], owner='mk1', parent='q3_mk_k1',
        self_assessment='CPL giảm 20%, chưa tới mục tiêu; số lead chỉ đạt 59% vì ngân sách tháng 8 bị cắt.',
        lessons='Chiến dịch nhắm lại (remarketing) có CPL thấp nhất, nên tăng tỷ trọng.'),
    obj('q3_i_vh1', 'Go-live thí điểm 10 phòng khám', 'individual', [
        kr('q3_i_vh1_k1', 'Go-live 10 phòng khám', 0, 10, 'phòng khám', final=7),
        kr('q3_i_vh1_k2', 'Đào tạo 50 lễ tân sử dụng hệ thống', 0, 50, 'người', final=52),
    ], owner='vh1', parent='q3_vh_k1',
        self_assessment='Đào tạo vượt kế hoạch; go-live chậm do chờ chuyển đổi dữ liệu.',
        lessons='Đào tạo lễ tân trước ngày go-live 1 tuần giúp giảm 50% yêu cầu hỗ trợ.'),
]

Q3_REVIEW = {
    'date': '2026-10-02',
    'went_well': '<ul><li>MRR đạt 2,4 tỷ đồng, đúng mục tiêu quý.</li>'
                 '<li>NPS đối tác tăng từ 38 lên 48 điểm nhờ bộ kịch bản hỗ trợ chuẩn.</li>'
                 '<li>Đào tạo lâm sàng vượt chỉ tiêu: 41 bác sĩ đối tác.</li>'
                 '<li>Kỷ luật check-in hằng tuần đạt trên 85%.</li></ul>',
    'to_improve': '<ul><li>Thí điểm đặt lịch online mới đạt 12/20 phòng khám.</li>'
                  '<li>Tuyển dụng vị trí kỹ thuật chậm (5/8).</li>'
                  '<li>Ngân sách marketing thay đổi giữa quý làm hụt 30% lead.</li></ul>',
    'lessons': '<ul><li>Khảo sát hạ tầng phần mềm phòng khám trước khi cam kết go-live.</li>'
               '<li>Chu kỳ bán hàng cho chuỗi lớn dài 8-10 tuần: đưa vào pipeline từ đầu quý.</li>'
               '<li>Đo NPS hằng tháng.</li></ul>',
    'decisions': '<ul><li>Chuyển 8 phòng khám chưa go-live sang OKR quý 4 của phòng Vận hành.</li>'
                 '<li>Khoá ngân sách quảng cáo theo quý với phòng Tài chính.</li>'
                 '<li>Thêm 1 kỹ sư tích hợp vào đội triển khai.</li></ul>',
}

# ----------------------------------------------------------------------
# Q4 2026: the running cycle
# ----------------------------------------------------------------------
BLOCK_CRM = 'Danh sách đầu mối liên hệ của 35 phòng khám mới chưa được cập nhật trên CRM.'
BLOCK_ONBOARD = 'Đội triển khai đang thiếu 1 kỹ sư, lịch onboarding tuần sau dồn 6 phòng khám.'
BLOCK_API = 'Phần mềm quản lý cũ (bản 2019) của 9 phòng khám không hỗ trợ webhook, phải đồng bộ lịch thủ công.'
BLOCK_BOARD = 'Hai chuỗi lớn ở Biên Hòa hoãn ký vì chờ HĐQT phê duyệt ngân sách quý 4.'

Q4_COMPANY = [
    obj('co_rev', 'Tăng trưởng doanh thu bền vững từ mạng lưới phòng khám đối tác', 'company', [
        kr('k_mrr', 'Doanh thu định kỳ hằng tháng (MRR) đạt 3,2 tỷ đồng', 2.4, 3.2, 'tỷ đồng', owner='kd_mgr'),
        kr('k_newclinics', 'Ký mới 25 phòng khám đối tác', 0, 25, 'phòng khám', owner='kd_mgr', method='objectives'),
        kr('k_renew', 'Tỷ lệ gia hạn hợp đồng đạt 92%', 85, 92, metric='percent', owner='ceo', profile='behind'),
    ], owner='ceo', tags=['growth'], contributor_depts=['mkt'],
        description='<p>Quý 4 là mùa cao điểm của nha khoa. DMAG tập trung ký mới phòng khám, '
                    'nâng cấp gói Premium và giữ chân khách hàng hiện hữu.</p>'),
    obj('co_cx', 'Mang lại trải nghiệm khách hàng xuất sắc', 'company', [
        kr('k_nps', 'NPS của phòng khám đối tác đạt 65 điểm', 48, 65, 'điểm', owner='cskh_mgr', method='objectives'),
        kr('k_response', 'Thời gian phản hồi yêu cầu hỗ trợ dưới 2 giờ', 6, 2, 'giờ', owner='cskh_mgr',
           profile='ahead'),
        kr('k_recall', 'Tỷ lệ bệnh nhân tái khám đúng hẹn đạt 80%', 62, 80, metric='percent', owner='ls_mgr',
           method='objectives'),
    ], owner='ceo', tags=['customer'], contributor_depts=['ls'],
        description='<p>Mỗi phòng khám đối tác và bệnh nhân của họ đều cảm nhận được sự chuyên nghiệp của DMAG.</p>'),
    obj('co_ops', 'Vận hành chuẩn hoá & số hoá toàn chuỗi', 'company', [
        kr('k_booking', '100% phòng khám đối tác dùng đặt lịch online', 0, 100, '%', owner='vh_mgr',
           method='objectives'),
        kr('k_sop', 'Chuẩn hoá và số hoá 40 quy trình SOP', 0, 40, 'quy trình', owner='admin',
           contributors=['vh_mgr', 'ls_mgr']),
        kr('k_cost', 'Giảm 15% chi phí vận hành trên mỗi phòng khám', 0, 15, '%', owner='tc_mgr',
           method='objectives'),
    ], owner='admin', okr_type='aspirational', tags=['digital'],
        description='<p>Tham vọng: mọi quy trình cốt lõi chạy trên nền tảng số, đo lường được.</p>'),
]

Q4_DEPARTMENTS = [
    obj('d_kd', 'Mở rộng mạng lưới phòng khám đối tác khu vực phía Nam', 'department', [
        kr('kd_contracts', 'Ký mới 25 hợp đồng phòng khám', 0, 25, 'hợp đồng', owner='kd_mgr'),
        kr('kd_demo', 'Thực hiện 120 buổi demo sản phẩm', 0, 120, 'buổi', owner='kd_mgr', profile='ahead',
           contributors=['kd1', 'kd2']),
        kr('kd_conv', 'Tỷ lệ chuyển đổi demo → hợp đồng đạt 25%', 12, 25, metric='percent', owner='kd_mgr',
           profile='behind'),
    ], dept='kd', parent='k_newclinics', tags=['growth'], contributor_depts=['mkt']),
    obj('d_kd2', 'Tăng giá trị khách hàng hiện hữu với gói Premium', 'department', [
        kr('kd_upsell', 'Nâng cấp 15 phòng khám lên gói Premium', 0, 15, 'phòng khám', owner='kd3'),
        kr('kd_upsell_rev', 'Doanh thu upsell đạt 450 triệu đồng', 0, 450, 'triệu đồng', owner='kd_mgr',
           profile='behind'),
    ], dept='kd', parent='k_mrr', okr_type='aspirational', tags=['growth']),
    obj('d_cskh', 'Hỗ trợ đối tác nhanh, chu đáo và chủ động', 'department', [
        kr('cs_nps', 'NPS đối tác đạt 65 điểm', 48, 65, 'điểm', owner='cskh_mgr'),
        kr('cs_fcr', '75% yêu cầu được giải quyết ngay lần liên hệ đầu tiên', 55, 75, metric='percent', owner='cs1'),
        kr('cs_calls', 'Gọi chăm sóc định kỳ 100% đối tác mỗi tháng', 40, 100, metric='percent', owner='cs2',
           profile='blocked', blocker=BLOCK_CRM),
    ], dept='cskh', parent='k_nps', tags=['customer']),
    obj('d_ls', 'Nâng chuẩn chất lượng điều trị tại phòng khám đối tác', 'department', [
        kr('ls_train', 'Đào tạo lâm sàng cho 60 bác sĩ đối tác', 0, 60, 'bác sĩ', owner='ls1', profile='ahead'),
        kr('ls_recall', 'Tỷ lệ tái khám đúng hẹn đạt 80%', 62, 80, metric='percent', owner='ls_mgr'),
        kr('ls_std', 'Ban hành bộ tiêu chuẩn vô khuẩn DMAG', metric='boolean', owner='ls2', profile='done'),
    ], dept='ls', parent='k_recall', tags=['quality']),
    obj('d_mkt', 'Tạo nguồn khách hàng tiềm năng chất lượng cho Kinh doanh', 'department', [
        kr('mk_mql', 'Thu hút 400 lead phòng khám đủ điều kiện (MQL)', 0, 400, 'lead', owner='mk1', profile='ahead'),
        kr('mk_cpl', 'Chi phí mỗi lead dưới 350 nghìn đồng', 600, 350, 'nghìn đồng', owner='mk1', profile='behind'),
        kr('mk_event', 'Tổ chức 3 hội thảo "Nha khoa số"', 0, 3, 'hội thảo', owner='mkt_mgr'),
    ], dept='mkt', parent='k_newclinics', okr_type='aspirational', tags=['growth'],
        contributor_users=['kd_mgr']),
    obj('d_vh', 'Triển khai đặt lịch online cho toàn bộ phòng khám đối tác', 'department', [
        kr('vh_project', 'Hoàn thành dự án "Triển khai hệ thống đặt lịch online"', 0, 100, '%', owner='vh2',
           method='tasks'),
        kr('vh_golive', '45 phòng khám go-live đặt lịch online', 12, 45, 'phòng khám', owner='vh1'),
        kr('vh_onboard', 'Thời gian onboarding phòng khám mới dưới 7 ngày', 14, 7, 'ngày', owner='vh_mgr',
           profile='blocked', blocker=BLOCK_ONBOARD),
    ], dept='vh', parent='k_booking', tags=['digital'], contributor_users=['cs1'],
        carried_from='q3_vh', carried_krs={'vh_golive': 'q3_vh_k1'}),
    obj('d_ns', 'Xây dựng đội ngũ gắn kết, sẵn sàng cho tăng trưởng', 'department', [
        kr('ns_enps', 'eNPS nội bộ đạt 40 điểm', 22, 40, 'điểm', owner='ns_mgr'),
        kr('ns_hire', 'Tuyển đủ 6 vị trí then chốt', 0, 6, 'vị trí', owner='ns1', profile='behind'),
        kr('ns_okr', '100% nhân sự hoàn thành khoá đào tạo OKR', 30, 100, metric='percent', owner='ns_mgr',
           profile='ahead'),
    ], dept='ns', parent='k_sop', tags=['people']),
    obj('d_tc', 'Tối ưu chi phí vận hành và dòng tiền', 'department', [
        kr('tc_cost', 'Giảm 15% chi phí vận hành mỗi phòng khám', 0, 15, metric='percent', owner='tc_mgr'),
        kr('tc_dso', 'Thời gian thu hồi công nợ còn 30 ngày', 45, 30, 'ngày', owner='tc1'),
        kr('tc_close', 'Đóng sổ kế toán tháng trong 5 ngày làm việc', 10, 5, 'ngày', owner='tc_mgr',
           profile='stalled'),
    ], dept='tc', parent='k_cost', visibility='department', tags=['growth']),
]

Q4_INDIVIDUALS = [
    obj('i_admin', 'Đưa OKR thành nhịp vận hành hằng tuần của toàn công ty', 'individual', [
        kr('i_admin_k1', 'Tỷ lệ check-in hằng tuần toàn công ty đạt 90%', 60, 90, metric='percent', profile='ahead'),
        kr('i_admin_k2', 'Tổ chức 6 buổi coaching OKR cho các phòng ban', 0, 6, 'buổi'),
    ], owner='admin', parent='k_sop', tags=['people', 'digital']),
    obj('i_kd1', 'Chinh phục các chuỗi nha khoa tại TP.HCM', 'individual', [
        kr('i_kd1_k1', 'Ký 10 hợp đồng phòng khám mới', 0, 10, 'hợp đồng', profile='ahead'),
        kr('i_kd1_k2', 'Thực hiện 50 buổi demo', 0, 50, 'buổi'),
    ], owner='kd1', parent='kd_contracts', tags=['growth']),
    obj('i_kd2', 'Phát triển đối tác tại Đồng Nai và Bình Dương', 'individual', [
        kr('i_kd2_k1', 'Ký 8 hợp đồng phòng khám', 0, 8, 'hợp đồng', profile='blocked', blocker=BLOCK_BOARD),
        kr('i_kd2_k2', 'Xây dựng 30 cơ hội bán hàng đủ điều kiện', 0, 30, 'cơ hội'),
    ], owner='kd2', parent='kd_contracts'),
    obj('i_kd3', 'Upsell gói Premium cho khách hàng hiện hữu', 'individual', [
        kr('i_kd3_k1', 'Tư vấn nâng cấp cho 40 phòng khám', 0, 40, 'phòng khám'),
        kr('i_kd3_k2', 'Doanh thu upsell cá nhân 240 triệu đồng', 0, 240, 'triệu đồng', profile='behind'),
    ], owner='kd3', parent='kd_upsell'),
    obj('i_kd3b', 'Mở thị trường Cần Thơ', 'individual', [
        kr('i_kd3b_k1', 'Khảo sát 30 phòng khám tại Cần Thơ', 0, 30, 'phòng khám'),
        kr('i_kd3b_k2', 'Ký 3 hợp đồng thí điểm', 0, 3, 'hợp đồng'),
    ], owner='kd3', parent='kd_contracts', okr_type='aspirational', state='to_approve'),
    obj('i_cs1', 'Giải quyết yêu cầu nhanh và dứt điểm', 'individual', [
        kr('i_cs1_k1', 'Tỷ lệ giải quyết ngay lần đầu (FCR) cá nhân đạt 80%', 60, 80, metric='percent'),
        kr('i_cs1_k2', 'CSAT sau hỗ trợ đạt 4,7/5', 4.2, 4.7, 'điểm', profile='ahead'),
    ], owner='cs1', parent='cs_fcr', tags=['customer']),
    obj('i_cs2', 'Chủ động chăm sóc 60 phòng khám đối tác', 'individual', [
        kr('i_cs2_k1', 'Gọi chăm sóc 60 phòng khám mỗi tháng', 20, 60, 'phòng khám', profile='blocked',
           blocker=BLOCK_CRM),
        kr('i_cs2_k2', 'Thu thập 12 câu chuyện thành công của khách hàng', 0, 12, 'câu chuyện', profile='none'),
    ], owner='cs2', parent='cs_calls', tags=['customer']),
    obj('i_ls1', 'Chuẩn hoá phác đồ chỉnh nha cho hệ thống đối tác', 'individual', [
        kr('i_ls1_k1', 'Đào tạo 30 bác sĩ chỉnh nha', 0, 30, 'bác sĩ', profile='ahead'),
        kr('i_ls1_k2', 'Ban hành phác đồ chỉnh nha chuẩn DMAG', metric='boolean'),
    ], owner='ls1', parent='ls_train', tags=['quality']),
    obj('i_ls2', 'Kiểm soát nhiễm khuẩn đạt chuẩn tại 100% phòng khám', 'individual', [
        kr('i_ls2_k1', 'Audit vô khuẩn 40 phòng khám', 0, 40, 'phòng khám'),
        kr('i_ls2_k2', 'Tỷ lệ phòng khám đạt chuẩn audit 95%', 70, 95, metric='percent', profile='behind'),
    ], owner='ls2', parent='ls_std', tags=['quality']),
    obj('i_mk1', 'Tối ưu quảng cáo tạo lead B2B', 'individual', [
        kr('i_mk1_k1', 'Thu 250 MQL từ quảng cáo', 0, 250, 'lead', profile='ahead'),
        kr('i_mk1_k2', 'Chi phí mỗi lead quảng cáo dưới 300 nghìn đồng', 650, 300, 'nghìn đồng', profile='behind'),
    ], owner='mk1', parent='mk_mql'),
    obj('i_mk2', 'Xây dựng thương hiệu chuyên gia "Nha khoa số"', 'individual', [
        kr('i_mk2_k1', 'Xuất bản 24 bài viết chuyên môn', 0, 24, 'bài'),
        kr('i_mk2_k2', 'Fanpage đạt 15.000 người theo dõi', 8000, 15000, 'người', profile='ahead'),
    ], owner='mk2', parent='mk_event'),
    obj('i_mk2b', 'Ra mắt podcast "Nha khoa số"', 'individual', [
        kr('i_mk2b_k1', 'Sản xuất 6 tập podcast', 0, 6, 'tập'),
        kr('i_mk2b_k2', 'Đạt 3.000 lượt nghe', 0, 3000, 'lượt nghe'),
    ], owner='mk2', parent='mk_event', okr_type='aspirational', state='draft'),
    obj('i_vh1', 'Go-live đặt lịch online cho phòng khám miền Nam', 'individual', [
        kr('i_vh1_k1', 'Go-live 20 phòng khám', 0, 20, 'phòng khám'),
        kr('i_vh1_k2', 'Đào tạo 100 lễ tân sử dụng hệ thống', 0, 100, 'người', profile='ahead'),
    ], owner='vh1', parent='vh_golive', tags=['digital']),
    obj('i_vh2', 'Đảm bảo hệ thống đặt lịch vận hành ổn định', 'individual', [
        kr('i_vh2_k1', 'Uptime hệ thống đặt lịch đạt 99,9%', 99.0, 99.9, metric='percent'),
        kr('i_vh2_k2', 'Lỗi đồng bộ lịch dưới 5 lỗi mỗi tuần', 30, 5, 'lỗi', profile='blocked', blocker=BLOCK_API),
    ], owner='vh2', parent='vh_project', tags=['digital']),
    obj('i_vh2b', 'Tự động hoá kiểm thử hệ thống đặt lịch', 'individual', [
        kr('i_vh2b_k1', 'Viết 120 kịch bản kiểm thử tự động', 0, 120, 'kịch bản'),
        kr('i_vh2b_k2', 'Thời gian kiểm thử hồi quy dưới 2 giờ', 16, 2, 'giờ'),
    ], owner='vh2', parent='vh_project', state='to_approve', tags=['digital']),
    obj('i_ns1', 'Tuyển dụng nhanh và đúng người', 'individual', [
        kr('i_ns1_k1', 'Tuyển 6 vị trí then chốt', 0, 6, 'vị trí', profile='behind'),
        kr('i_ns1_k2', 'Thời gian tuyển trung bình dưới 30 ngày', 50, 30, 'ngày'),
    ], owner='ns1', parent='ns_hire', tags=['people']),
    obj('i_ns1b', 'Phát triển năng lực HRBP cá nhân', 'individual', [
        kr('i_ns1b_k1', 'Hoàn thành chứng chỉ HRBP', metric='boolean'),
        kr('i_ns1b_k2', 'Thực hiện 12 buổi coaching 1:1 với quản lý', 0, 12, 'buổi'),
    ], owner='ns1', parent='ns_enps', visibility='private', tags=['people']),
    obj('i_tc1', 'Thu hồi công nợ đúng hạn', 'individual', [
        kr('i_tc1_k1', 'Tỷ lệ công nợ quá hạn dưới 5%', 18, 5, metric='percent'),
        kr('i_tc1_k2', 'Đối soát 100% hoá đơn hằng tháng', 60, 100, metric='percent', profile='ahead'),
    ], owner='tc1', parent='tc_dso'),
]

# Objectives created from templates (template xmlid, fallback level, values)
TEMPLATE_OBJECTIVES = [
    {'template': 'okr_scale_template.okr_tpl_care_agent', 'level': 'individual', 'owner': 'cs2',
     'parent': 'cs_calls', 'state': 'running', 'name': 'Mỗi cuộc gọi chăm sóc là một trải nghiệm ấm áp'},
    {'template': 'okr_scale_template.okr_tpl_care_complaint', 'level': 'department', 'dept': 'cskh',
     'parent': 'k_response', 'state': 'to_approve', 'name': 'Mọi khiếu nại được lắng nghe và xử lý nhanh, tận tâm'},
]

PORTAL_OBJECTIVE = obj('p_ad', 'Tăng 30% bệnh nhân chỉnh nha tại Nha khoa Ánh Dương', 'department', [
    kr('pa_patients', 'Bệnh nhân chỉnh nha mới đạt 52 ca mỗi tháng', 40, 52, 'ca/tháng', owner='pt_edit'),
    kr('pa_close', 'Tỷ lệ chốt ca tư vấn chỉnh nha đạt 45%', 30, 45, metric='percent', owner='kd3'),
    kr('pa_booking', 'Kích hoạt đặt lịch & nhắc hẹn tự động tại Ánh Dương', metric='boolean', owner='vh1',
       profile='done'),
], dept='kd', parent='kd_upsell', tags=['customer', 'growth'],
    description='<p>Mục tiêu chung giữa DMAG và Nha khoa Ánh Dương: tăng 30% số bệnh nhân chỉnh nha mới nhờ '
                'quy trình tư vấn chuẩn, đặt lịch online và nhắc hẹn tự động.</p>')

PORTAL_CHECKINS = [
    # week offset from the first Q4 week, value, confidence, achievements, blockers, next steps
    (0, 42, '7', 'Tháng 9 đạt 42 ca chỉnh nha mới, nhiều khách đến từ chương trình ưu đãi khai giảng.', '',
     'Chạy chương trình tư vấn chỉnh nha miễn phí cuối tuần.'),
    (1, 45, '8', 'Tư vấn miễn phí cuối tuần mang về 11 lượt khám, chốt 6 ca.', '',
     'Đào tạo thêm 1 tư vấn viên ca tối.'),
]

Q1_DRAFT = obj('q1_north', 'Mở rộng mạng lưới DMAG ra thị trường miền Bắc', 'company', [
    kr('q1_n1', 'Ký 15 phòng khám đối tác tại Hà Nội', 0, 15, 'phòng khám', owner='kd_mgr'),
    kr('q1_n2', 'Mở văn phòng đại diện tại Hà Nội', metric='boolean', owner='vh_mgr'),
], owner='ceo', state='draft', okr_type='aspirational', tags=['growth'])

# ----------------------------------------------------------------------
# Check-ins and weekly texts
# ----------------------------------------------------------------------
ACHIEVEMENTS = {
    'bgd': ['Rà soát pipeline cùng các trưởng phòng, ưu tiên 5 chuỗi lớn.',
            'Họp với 3 đối tác chiến lược về gói Premium.',
            'Chốt kế hoạch ngân sách quý 4 với phòng Tài chính.'],
    'kd': ['Demo cho chuỗi Nha khoa Kim Long và Smile Care, khách đánh giá cao tính năng nhắc hẹn.',
           'Chốt 2 hợp đồng tại Quận 7 và Thủ Đức.',
           'Gặp trực tiếp 6 phòng khám tại Bình Dương, 3 phòng khám hẹn demo.',
           'Hoàn thiện bảng giá gói Premium kèm trả góp 6 tháng.'],
    'cskh': ['Xử lý 186 yêu cầu hỗ trợ, 78% giải quyết ngay lần đầu.',
             'Gọi chăm sóc 24 phòng khám, ghi nhận 5 góp ý về báo cáo doanh thu.',
             'Cập nhật 12 bài hướng dẫn trên trung tâm trợ giúp.',
             'Khảo sát NPS tháng 10 cho 120 phòng khám.'],
    'ls': ['Tổ chức lớp đào tạo chỉnh nha trong suốt cho 12 bác sĩ.',
           'Audit vô khuẩn 6 phòng khám khu vực Gò Vấp.',
           'Hoàn thiện checklist tái khám sau niềng răng.',
           'Phối hợp Vận hành cài nhắc hẹn tái khám tự động.'],
    'mkt': ['Chiến dịch "Nha khoa số 2026" mang về 64 lead mới.',
            'Tối ưu nhóm quảng cáo, CPL giảm 9% so với tuần trước.',
            'Xuất bản 3 bài viết chuyên môn và 1 case study.',
            'Chốt địa điểm hội thảo tại Quận 1 với 120 chỗ.'],
    'vh': ['Go-live 4 phòng khám khu vực Bình Thạnh và Phú Nhuận.',
           'Đào tạo 26 lễ tân sử dụng màn hình đặt lịch.',
           'Sửa lỗi đồng bộ lịch hẹn cho phiên bản Android.',
           'Hoàn thành bộ chuyển đổi dữ liệu từ phần mềm cũ.'],
    'ns': ['Phỏng vấn 9 ứng viên cho 3 vị trí kỹ thuật.',
           'Tổ chức khảo sát eNPS quý 4, 92% nhân sự tham gia.',
           '18 nhân sự hoàn thành khoá đào tạo OKR cơ bản.'],
    'tc': ['Đối soát xong hoá đơn tháng 9 cho 210 phòng khám.',
           'Gửi nhắc nợ tự động cho 34 khách hàng sắp đến hạn.',
           'Rà soát hợp đồng nhà cung cấp, đề xuất cắt giảm 3 khoản phí.'],
}

NEXT_STEPS = {
    'bgd': ['Duyệt kế hoạch mở rộng miền Bắc cho quý 1/2027.', 'Họp 1:1 với các trưởng phòng có OKR rủi ro.'],
    'kd': ['Chốt hợp đồng với chuỗi Nha khoa Kim Long.', 'Lên lịch 8 buổi demo cho phòng khám tại Đồng Nai.',
           'Đề xuất ưu đãi gia hạn sớm cho khách hàng hết hạn tháng 11.'],
    'cskh': ['Hoàn tất gọi chăm sóc nhóm phòng khám mới ký.', 'Phân tích nguyên nhân 15 phiếu NPS thấp.',
             'Thử nghiệm chatbot trả lời câu hỏi thường gặp.'],
    'ls': ['Mở lớp đào tạo chỉnh nha khu vực Cần Thơ.', 'Audit 8 phòng khám khu vực Thủ Đức.',
           'Gửi bản nháp phác đồ chỉnh nha cho Hội đồng chuyên môn.'],
    'mkt': ['Chạy thử nghiệm A/B trang đích mới.', 'Gửi thư mời hội thảo cho 600 phòng khám.',
            'Sản xuất video case study Nha khoa Ánh Dương.'],
    'vh': ['Go-live 5 phòng khám khu vực Thủ Đức.', 'Hoàn thiện tài liệu onboarding rút gọn 5 bước.',
           'Kiểm thử tải hệ thống đặt lịch trước đợt cao điểm cuối năm.'],
    'ns': ['Chốt offer Trưởng nhóm triển khai.', 'Triển khai đào tạo OKR cho khối Vận hành.'],
    'tc': ['Đóng sổ tháng 10 trước ngày 7/11.', 'Trình phương án tối ưu chi phí server.'],
}

WEEKLY_SUMMARIES = {
    'bgd': ['Tuần làm việc tập trung vào pipeline chuỗi lớn và ưu tiên nguồn lực cho dự án đặt lịch online.',
            'Các phòng ban check-in đầy đủ, rủi ro chính nằm ở tốc độ onboarding phòng khám.'],
    'kd': ['Pipeline tăng tốt, nhiều phòng khám quan tâm gói Premium nhờ tính năng nhắc hẹn tự động.',
           'Tuần nhiều buổi demo, tỷ lệ chốt chưa cao ở nhóm phòng khám nhỏ.'],
    'cskh': ['Lượng yêu cầu hỗ trợ tăng 20% sau đợt go-live nhưng vẫn giữ được thời gian phản hồi.',
             'Tuần ổn định, NPS các phòng khám mới go-live khá cao.'],
    'ls': ['Hoạt động đào tạo đúng tiến độ, các bác sĩ đối tác phản hồi rất tích cực.',
           'Audit vô khuẩn phát hiện 2 phòng khám cần khắc phục, đã có kế hoạch.'],
    'mkt': ['Lead tăng đều nhờ chiến dịch mới, chi phí mỗi lead vẫn cao hơn mục tiêu.',
            'Chuẩn bị hội thảo "Nha khoa số" đúng tiến độ.'],
    'vh': ['Go-live đúng lịch nhưng đội triển khai đang quá tải.',
           'Hệ thống ổn định, còn lỗi đồng bộ với phần mềm cũ ở một số phòng khám.'],
    'ns': ['Tuyển dụng vị trí kỹ thuật vẫn chậm, các vị trí khác đúng tiến độ.',
           'Khảo sát eNPS cho tín hiệu tích cực về văn hoá ghi nhận.'],
    'tc': ['Công nợ quá hạn tiếp tục giảm, đóng sổ tháng còn chậm do chờ chứng từ chi nhánh.',
           'Tuần tập trung đối soát và nhắc nợ.'],
}

# Help asked in the weekly check-in of the current week, by person
HELP_NEEDED = {
    'kd3': 'Cần chị Mai hỗ trợ đàm phán giá gói Premium với chuỗi 4 phòng khám Ánh Dương.',
    'vh_mgr': 'Cần BGĐ duyệt tuyển gấp 1 kỹ sư triển khai để kịp lịch go-live tháng 11.',
    'cs1': 'Cần phòng Vận hành chia sẻ lịch go-live sớm 1 tuần để chuẩn bị ca trực.',
}

# Weekly check-in submitted this week (the check-in day is still to come for the others)
CURRENT_WEEK_SUBMITTERS = ['admin', 'kd_mgr', 'kd1', 'kd3', 'cskh_mgr', 'cs1', 'ls_mgr', 'ls1', 'mkt_mgr',
                           'mk1', 'vh_mgr', 'vh1', 'tc_mgr', 'ns_mgr']
# People who missed the weekly check-in of a past week: {weeks ago: [keys]}
MISSED_WEEKS = {1: ['ns1', 'mk2'], 2: ['tc1'], 3: ['kd2'], 4: ['cs2'], 5: ['mk2']}

MANAGER_FEEDBACK = [
    'Tốt lắm, giữ nhịp này nhé!',
    'Cảm ơn em, tuần sau mình trao đổi thêm trong buổi 1:1.',
    'Rất tốt. Nhớ cập nhật rủi ro sớm nếu đối tác đổi lịch.',
    'Tiến độ ổn, cần tập trung hơn vào chỉ số chuyển đổi.',
]

# ----------------------------------------------------------------------
# CFR
# ----------------------------------------------------------------------
RECOGNITIONS = [
    # sender, receivers, core values, points, objective key, message, days ago, likes
    ('ceo', ['kd_mgr'], ['ownership'], 30, 'd_kd',
     'Chị Mai và team Kinh doanh chốt 3 hợp đồng chuỗi ngay tuần đầu quý. Tinh thần dẫn dắt tuyệt vời!', 1, 9),
    ('kd_mgr', ['kd1'], ['customer'], 20, 'i_kd1',
     'Đức Anh xử lý xuất sắc buổi demo cho chuỗi Nha khoa Kim Long, khách hàng ký ngay tại chỗ.', 2, 6),
    ('cskh_mgr', ['cs1'], ['customer', 'ownership'], 20, 'i_cs1',
     'Tâm ở lại đến 9 giờ tối để giúp phòng khám Thủ Đức khôi phục lịch hẹn. Cảm ơn em rất nhiều!', 3, 8),
    ('vh_mgr', ['vh2'], ['innovation', 'ownership'], 25, 'i_vh2',
     'Nhật tự viết công cụ đồng bộ tạm thời khi API cũ không hỗ trợ webhook, giảm 70% lỗi đồng bộ.', 4, 7),
    ('mkt_mgr', ['mk1', 'mk2'], ['teamwork'], 15, 'd_mkt',
     'Hội thảo "Nha khoa số" tại Quận 1 thu hút 120 bác sĩ. Cảm ơn Huy và Trâm đã chuẩn bị chu đáo.', 5, 10),
    ('kd1', ['mk1'], ['teamwork'], 10, 'd_kd',
     'Lead từ chiến dịch của Huy rất chất lượng: 4/10 lead đã lên lịch demo!', 5, 4),
    ('ls_mgr', ['ls2'], ['integrity', 'customer'], 20, 'd_ls',
     'Phúc hoàn thành bộ tiêu chuẩn vô khuẩn DMAG sớm 3 tuần, chuẩn mực và rất chi tiết.', 6, 6),
    ('admin', ['vh1', 'vh2'], ['teamwork'], 20, 'd_vh',
     'Team triển khai go-live 6 phòng khám trong một tuần mà không có sự cố nào. Quá đỉnh!', 7, 11),
    ('cs2', ['vh1'], ['teamwork'], 10, False,
     'Cảm ơn chị Yến đã hỗ trợ đào tạo lễ tân phòng khám Bình Thạnh ngoài giờ.', 8, 3),
    ('ns_mgr', ['ns1'], ['ownership'], 15, 'i_ns1',
     'Vinh chốt được ứng viên Trưởng nhóm triển khai chỉ sau 18 ngày tuyển dụng.', 8, 5),
    ('tc_mgr', ['tc1'], ['integrity'], 15, 'i_tc1',
     'Phương phát hiện sai lệch đối soát 120 triệu đồng và xử lý minh bạch, kịp thời.', 9, 4),
    ('kd2', ['kd3'], ['teamwork'], 10, False,
     'Khoa chia sẻ bộ slide upsell Premium giúp mình chốt được phòng khám ở Dĩ An.', 10, 3),
    ('ceo', ['cskh_mgr', 'cs1', 'cs2'], ['customer'], 15, 'co_cx',
     'NPS tháng 9 tăng 6 điểm: công sức của cả đội Chăm sóc khách hàng. Rất tự hào về các bạn!', 11, 12),
    ('mk2', ['ls1'], ['innovation'], 10, False,
     'Chị Hân viết loạt bài "Chỉnh nha trong suốt" đạt hơn 40.000 lượt đọc!', 11, 5),
    ('vh1', ['cs1'], ['customer'], 10, 'd_vh',
     'Tâm phản hồi nhanh mọi câu hỏi của phòng khám sau go-live, giúp đối tác rất yên tâm.', 0, 2),
    ('vh_mgr', ['admin'], ['teamwork'], 20, 'i_admin',
     'Anh Tuấn gỡ vướng nhân sự cho đội Vận hành ngay trong ngày, cả đội giữ được lịch go-live.', 2, 7),
    ('ns_mgr', ['admin'], ['innovation'], 15, 'i_admin',
     'Buổi coaching OKR của anh Tuấn giúp phòng Nhân sự viết lại KR rõ ràng, đo được.', 4, 5),
    ('admin', ['ls_mgr'], ['innovation'], 20, 'co_ops',
     'Anh Thịnh số hoá 8 SOP lâm sàng đầu tiên, làm mẫu cho toàn hệ thống.', 12, 6),
]

FEEDBACKS = [
    # author, recipient, type, objective key, content, days ago
    ('kd_mgr', 'kd2', 'constructive', 'i_kd2',
     '<p>Em nên chuẩn bị sẵn phương án trả góp và bảng ROI trước khi gặp HĐQT các chuỗi ở Biên Hòa. '
     'Chị sẽ đi cùng em buổi gặp tuần sau.</p>', 3),
    ('cskh_mgr', 'cs2', 'suggestion', 'i_cs2',
     '<p>Thử chia danh sách gọi chăm sóc theo khu vực và gọi theo khung giờ 10h-11h, '
     'tỷ lệ bắt máy sẽ cao hơn.</p>', 4),
    ('vh_mgr', 'vh1', 'praise', 'i_vh1',
     '<p>Buổi đào tạo lễ tân của Yến rất dễ hiểu, các phòng khám đều khen. Hãy ghi lại thành video mẫu nhé!</p>', 5),
    ('ceo', 'admin', 'praise', 'co_ops',
     '<p>Dashboard OKR giúp BGĐ nắm tình hình mỗi sáng thứ Hai chỉ trong 10 phút. Cảm ơn Tuấn!</p>', 6),
    ('kd1', 'kd_mgr', 'suggestion', 'd_kd',
     '<p>Em đề xuất họp pipeline 15 phút mỗi sáng thứ Hai để cả team cùng ưu tiên khách hàng nóng.</p>', 2),
]

FEEDBACK_REQUEST = ('ns_mgr', 'tc_mgr', 'ns1',
                    'Anh Đạt góp ý giúp em về cách Vinh phối hợp tuyển vị trí Kế toán tổng hợp nhé.')

CONVERSATIONS = [
    # manager, employee, objective keys, state, day offset from today, hour (local), cadence, notes, actions
    ('kd_mgr', 'kd2', ['i_kd2'], 'done', -6, 9, 'biweekly',
     '<p>Hai chuỗi lớn ở Biên Hòa chờ HĐQT duyệt ngân sách. Hà vẫn giữ liên lạc hằng tuần.</p>'
     '<p>Hà tự tin đạt 6/8 hợp đồng nếu có gói trả góp.</p>',
     '<ul><li>Chị Mai đi cùng buổi gặp HĐQT tuần sau.</li><li>Hà chuẩn bị bảng ROI theo từng chuỗi.</li></ul>'),
    ('cskh_mgr', 'cs2', ['i_cs2'], 'done', -5, 14, 'biweekly',
     '<p>CRM thiếu đầu mối liên hệ của 35 phòng khám mới, Hồng mất nhiều thời gian tra cứu.</p>',
     '<ul><li>Lan làm việc với Kinh doanh để bổ sung dữ liệu trước thứ Sáu.</li></ul>'),
    ('vh_mgr', 'vh2', ['i_vh2'], 'done', -7, 10, 'weekly',
     '<p>Công cụ đồng bộ tạm thời chạy tốt. Cần kế hoạch nâng cấp cho 9 phòng khám dùng phần mềm cũ.</p>',
     '<ul><li>Nhật viết đề xuất nâng cấp kèm chi phí.</li></ul>'),
    ('ceo', 'kd_mgr', ['d_kd', 'd_kd2'], 'done', -8, 15, 'monthly',
     '<p>Pipeline quý 4 đủ cho 28 hợp đồng. Upsell Premium chậm hơn kế hoạch.</p>',
     '<ul><li>Thiết kế ưu đãi nâng cấp Premium trước 20/10.</li></ul>'),
    ('kd_mgr', 'kd1', ['i_kd1'], 'planned', 1, 9, 'biweekly', False, False),
    ('ls_mgr', 'ls1', ['i_ls1'], 'planned', 2, 10, 'biweekly', False, False),
    ('mkt_mgr', 'mk1', ['i_mk1'], 'planned', 2, 14, 'biweekly', False, False),
    ('admin', 'vh_mgr', ['d_vh'], 'planned', 3, 9, 'weekly', False, False),
]

# ----------------------------------------------------------------------
# Rewards
# ----------------------------------------------------------------------
REWARD_ITEMS = [
    # key, name, category xmlid suffix, cost, icon, caption, description, limited stock
    ('coffee', 'Voucher cà phê 100.000đ', 'voucher', 80, 'coffee', 'Voucher cà phê',
     'Voucher dùng tại các chuỗi cà phê gần văn phòng. Gửi qua e-mail trong 2 ngày làm việc.', 0),
    ('shirt', 'Áo thun DMAG phiên bản 2026', 'gift', 60, 'shirt', 'Áo thun DMAG',
     'Áo cotton in logo DMAG, đủ size S - XXL. Ghi size vào phần ghi chú.', 25),
    ('tooth', 'Bộ chăm sóc răng miệng cao cấp', 'gift', 120, 'tooth', 'Bộ chăm sóc răng',
     'Bàn chải điện, máy tăm nước mini và kem đánh răng chuyên dụng.', 8),
    ('dinner', 'Bữa tối gia đình 1.000.000đ', 'voucher', 250, 'dinner', 'Bữa tối gia đình',
     'Phiếu ăn tối cho gia đình tại nhà hàng đối tác của DMAG.', 0),
    ('day_off', 'Thêm 1 ngày nghỉ phép', 'experience', 300, 'calendar', 'Thêm 1 ngày nghỉ',
     'Một ngày nghỉ phép có lương, sắp xếp với quản lý trực tiếp.', 0),
    ('headphones', 'Tai nghe không dây chống ồn', 'gift', 400, 'headphones', 'Tai nghe chống ồn',
     'Tai nghe bluetooth chống ồn chủ động, pin 30 giờ.', 3),
    ('course', 'Khoá học chuyên môn (tối đa 3 triệu đồng)', 'experience', 500, 'course', 'Khoá học chuyên môn',
     'Tự chọn một khoá học trong danh sách được phòng Nhân sự duyệt.', 0),
    ('mystery', 'Hộp quà bí mật cuối năm', 'gift', 150, 'gift', 'Hộp quà bí mật',
     'Món quà bất ngờ do Ban Giám đốc chọn. Số lượng có hạn!', 2),
]

POINT_GRANTS = [
    # description, {person key: points}, days ago
    ('Điểm chào mừng chương trình DMAG Rewards', 'all:100', 40),
    ('Thưởng kỷ luật check-in quý 3', {
        'kd1': 120, 'cs1': 150, 'vh1': 120, 'ls1': 140, 'mk1': 90, 'kd_mgr': 100, 'tc1': 110, 'ls2': 130,
        'vh2': 120, 'ns1': 60, 'cs2': 80, 'kd3': 90, 'mk2': 70, 'kd2': 60, 'admin': 150,
    }, 12),
    ('Thưởng dự án go-live đặt lịch online đợt 1', {'vh1': 150, 'vh2': 200, 'vh_mgr': 100, 'cs1': 50}, 6),
]

REDEMPTIONS = [
    # person, item key, quantity, final state, note, reason
    ('kd1', 'coffee', 1, 'delivered', False, False),
    ('cs1', 'shirt', 1, 'delivered', 'Size M', False),
    ('vh2', 'day_off', 1, 'approved', 'Nghỉ ngày 30/10 sau đợt go-live', False),
    ('ls2', 'tooth', 1, 'requested', False, False),
    ('vh1', 'headphones', 1, 'requested', False, False),
    ('ns1', 'mystery', 1, 'rejected', False,
     'Hộp quà bí mật đợt này đã được đổi hết trước khi yêu cầu được xử lý, điểm đã được hoàn lại cho bạn.'),
    ('kd3', 'tooth', 1, 'cancelled', False, False),
    ('admin', 'coffee', 2, 'delivered', False, False),
]

# Tasks of the online booking project: name, assignee, done, allocated hours, stage
PROJECT = {
    'name': 'Triển khai hệ thống đặt lịch online',
    'stages': ['Cần làm', 'Đang thực hiện', 'Kiểm thử', 'Hoàn thành'],
    'tasks': [
        ('Khảo sát quy trình đặt lịch tại 10 phòng khám mẫu', 'vh1', True, 16, 'Hoàn thành'),
        ('Thiết kế luồng đặt lịch trên website và Zalo OA', 'vh2', True, 24, 'Hoàn thành'),
        ('Tích hợp API lịch hẹn với phần mềm quản lý phòng khám', 'vh2', True, 40, 'Hoàn thành'),
        ('Xây dựng tính năng nhắc hẹn tự động qua SMS/Zalo', 'vh2', True, 32, 'Hoàn thành'),
        ('Chuẩn bị tài liệu hướng dẫn cho lễ tân', 'vh1', True, 12, 'Hoàn thành'),
        ('Bộ chuyển đổi dữ liệu từ phần mềm cũ (bản 2019)', 'vh2', False, 40, 'Đang thực hiện'),
        ('Kiểm thử tải 5.000 lịch hẹn đồng thời', 'vh2', False, 16, 'Kiểm thử'),
        ('Go-live đợt 2: 10 phòng khám khu vực Thủ Đức', 'vh1', False, 24, 'Đang thực hiện'),
        ('Đào tạo lễ tân đợt 2 (40 người)', 'vh1', False, 16, 'Cần làm'),
        ('Dashboard tỉ lệ đặt lịch online cho chủ phòng khám', 'vh2', False, 24, 'Cần làm'),
        ('Go-live đợt 3: phòng khám khu vực Đồng Nai, Bình Dương', 'vh1', False, 24, 'Cần làm'),
        ('Nghiệm thu và tổng kết dự án', 'vh_mgr', False, 8, 'Cần làm'),
    ],
}

OBJECTIVE_COMMENTS = [
    # objective key, author, message, days ago
    ('co_rev', 'ceo', 'Tuần này ưu tiên tối đa cho 5 chuỗi lớn trong pipeline. Cần hỗ trợ gì cứ báo anh.', 4),
    ('co_rev', 'kd_mgr', 'Đã chốt thêm 2 hợp đồng ở Quận 7, dự kiến tuần sau ký tiếp chuỗi Kim Long.', 3),
    ('co_ops', 'vh_mgr', 'Đội triển khai cần thêm 1 kỹ sư để giữ lịch go-live tháng 11.', 2),
    ('d_vh', 'admin', 'Đã đưa đề xuất tuyển kỹ sư triển khai vào cuộc họp BGĐ thứ Năm.', 1),
]

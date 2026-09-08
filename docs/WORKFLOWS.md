# Luồng nghiệp vụ sau khi hoàn thiện

## 1. Bệnh nhân – đặt lịch
1. Đăng ký / đăng nhập.
2. Chọn chuyên khoa.
3. Chọn bác sĩ.
4. Chọn ngày và khung giờ còn trống.
5. Nhập lý do khám.
6. Xác nhận đặt lịch.
7. Xem mã lịch, số điện thoại và trạng thái trong Lịch của tôi.
8. Với lịch CONFIRMED: được đổi lịch hoặc hủy lịch.
9. Sau khi khám xong: xem chẩn đoán, ghi chú và đơn thuốc.

## 2. Lễ tân – tiếp nhận
1. Chọn ngày làm việc.
2. Tìm lịch theo mã lịch, mã bệnh nhân, họ tên, số điện thoại hoặc email.
3. Mở chi tiết để xác nhận thông tin bệnh nhân, bác sĩ, phòng, thời gian và lý do khám.
4. Bấm Tiếp nhận để chuyển CONFIRMED → CHECKED_IN → WAITING.
5. Bệnh nhân đến trễ được hiển thị số phút trễ và xếp ưu tiên sau lịch đúng giờ.
6. Sau 15 phút kể từ giờ hẹn có thể đánh dấu Không đến khám → NO_SHOW.
7. Bệnh nhân không có lịch có thể tra cứu hồ sơ và tạo Khám không đặt lịch → WALK_IN → WAITING.
8. Hàng chờ hiển thị theo ưu tiên: lịch đúng giờ → bệnh nhân trễ → khám không đặt lịch.
9. Nhân viên có thể gọi bệnh nhân tiếp theo.

## 3. Bác sĩ – khám bệnh
1. Xem danh sách bệnh nhân hôm nay.
2. Theo dõi hàng chờ của chính bác sĩ.
3. Bắt đầu khám từ WAITING → IN_PROGRESS.
4. Nhập chẩn đoán, ghi chú và đơn thuốc / hướng dẫn.
5. Lưu kết quả và chuyển IN_PROGRESS → COMPLETED.
6. Không cho phép CANCELLED / NO_SHOW / COMPLETED bắt đầu khám.
7. Không cho phép một bác sĩ có nhiều lượt IN_PROGRESS cùng lúc.
8. Quản lý ca làm việc và ngày nghỉ; Booking chỉ sinh slot theo lịch làm việc.

## 4. Trạng thái hiển thị tiếng Việt
- CONFIRMED: Đã xác nhận
- CHECKED_IN: Đã tiếp nhận
- WAITING: Đang chờ khám
- IN_PROGRESS: Đang khám
- COMPLETED: Đã khám xong
- CANCELLED: Đã hủy
- NO_SHOW: Không đến khám

WALK_IN là **loại lượt khám**, hiển thị là **Khám không đặt lịch**, không phải trạng thái.

## 5. Ghi chú
Tài liệu nhóm hiện không đặc tả chức năng gửi nhắc lịch trước 1 giờ, vì vậy bản này không giả lập một cơ chế reminder 1 giờ như một nghiệp vụ bắt buộc.

## Luồng thanh toán
1. Bệnh nhân chọn chuyên khoa -> bác sĩ -> dịch vụ -> ngày/giờ -> lý do khám.
2. Hệ thống hiển thị giá niêm yết của dịch vụ trước khi xác nhận.
3. Bệnh nhân chọn:
   - Thanh toán tại cơ sở: tạo giao dịch UNPAID.
   - Thanh toán QR: tạo giao dịch PENDING và hiển thị QR mô phỏng cùng số tiền, mã giao dịch.
4. Sau khi demo xác nhận thanh toán QR: PENDING -> PAID.
5. Nếu lịch đã thanh toán bị hủy hoặc chuyển NO_SHOW: PAID/PENDING -> REFUND_PENDING để nhân viên xử lý hoàn tiền.
6. Thanh toán QR trong đồ án là mô phỏng, không kết nối ngân hàng thật.


## Quản trị viên

Admin có màn hình quản trị tổng quan và quản lý dữ liệu nền: tìm/chỉnh sửa hồ sơ bệnh nhân, chỉnh thông tin bác sĩ và chuyên khoa, quản lý dịch vụ/bảng giá niêm yết, điều chỉnh ca làm việc/ngày nghỉ của bác sĩ, và đổi ngày/khung giờ appointment khi slot mới hợp lệ. Giá dịch vụ được lưu trong database và snapshot vào thanh toán khi tạo lịch. Các trạng thái appointment vẫn giữ nguyên tên chuẩn: CONFIRMED, CHECKED_IN, WAITING, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW; WALK_IN là loại lượt khám.

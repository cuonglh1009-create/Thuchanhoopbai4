# /****************/
# MSSV: 202418859
# Họ tên : Lê Hùng Cường
# /****************/
"""Hệ thống tính lương và thưởng nhân sự."""
import math
from abc import ABC, abstractmethod
from typing import Dict, Optional, overload

DEFAULT_DEPT = "Unassigned"


# Kiểm tra dữ liệu
def text(value, name: str) -> str:
    """Chuỗi không rỗng. Sai kiểu -> TypeError, rỗng -> ValueError."""
    if not isinstance(value, str):
        raise TypeError(f"{name} phải là chuỗi")
    if not value.strip():
        raise ValueError(f"{name} không được rỗng")
    return value.strip()


def number(value, name: str, lo: float = 0.0, hi: Optional[float] = None,
           lo_open: bool = False) -> float:
    """Số hữu hạn trong [lo; hi] (hoặc (lo; hi] nếu lo_open)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} phải là số")
    if not math.isfinite(value) or (value <= lo if lo_open else value < lo) \
            or (hi is not None and value > hi):
        raise ValueError(f"{name} không hợp lệ")
    return float(value)


def money(v: float) -> str:
    return f"{round(v):,}".replace(",", ".") + " VND"


#  Lớp cơ sở trừu tượng
class Employee(ABC):
    """Lớp cơ sở TRỪU TƯỢNG (A.8.4): giữ dữ liệu chung, bảo vệ bất biến
    (mã/tên/phòng ban không rỗng, thưởng >= 0), quản lý thưởng.

    Quyết định thiết kế (A.5): chỉ lưu TỔNG thưởng (monthlyBonus). Các công thức
    chỉ cần tổng, đề không yêu cầu truy vết từng khoản nên không cần lớp lịch sử.

    Nạp chồng constructor (A.4): Python không có overload constructor, dùng tham số
    mặc định: Employee(id, name) và Employee(id, name, department)."""

    def __init__(self, employee_id: str, full_name: str, department: str = DEFAULT_DEPT):
        self._employee_id = text(employee_id, "Mã nhân sự")
        self._full_name = text(full_name, "Họ tên")
        self._department = text(department, "Phòng ban")
        self._monthly_bonus = 0.0

    # Chỉ đọc: không cho sửa trực tiếp, mọi thay đổi thưởng đi qua add_bonus/reset_bonus
    employee_id = property(lambda self: self._employee_id)
    full_name = property(lambda self: self._full_name)
    department = property(lambda self: self._department)
    monthly_bonus = property(lambda self: self._monthly_bonus)

    #  Nạp chồng addBonus
    @overload
    def add_bonus(self, amount: float) -> None: ...
    @overload
    def add_bonus(self, amount: float, reason: str) -> None: ...
    @overload
    def add_bonus(self, rate: float, reference_amount: float, reason: str) -> None: ...

    def add_bonus(self, *args) -> None:
        """(1) amount | (2) amount, reason | (3) rate, reference_amount, reason.
        Mọi kiểm tra chạy trước khi đổi trạng thái nên lỗi không làm cộng dở dang."""
        if len(args) == 1:
            amount = args[0]
        elif len(args) == 2:
            amount = args[0]
            text(args[1], "Lý do thưởng")
        elif len(args) == 3:
            rate, reference, reason = args
            number(rate, "Tỷ lệ thưởng", 0, 0.5, lo_open=True)      # 0 < rate <= 0,5
            number(reference, "Giá trị tham chiếu", 0, lo_open=True)  # > 0
            text(reason, "Lý do thưởng")
            amount = rate * reference
        else:
            raise TypeError("add_bonus nhận 1, 2 hoặc 3 đối số")
        self._monthly_bonus += number(amount, "Khoản thưởng", 0, lo_open=True)  # amount > 0

    def reset_bonus(self) -> None:
        """Đặt lại thưởng khi bắt đầu kỳ lương mới."""
        self._monthly_bonus = 0.0

    #  Hành vi chung, lớp dẫn xuất ghi đè
    @abstractmethod
    def calculate_gross_pay(self) -> float: ...

    @abstractmethod
    def get_employee_type(self) -> str: ...

    def display_payroll_info(self) -> None:
        self._show()

    def _show(self, *details: str) -> None:
        print(f"[{self.get_employee_type()}] {self._employee_id} - {self._full_name} "
              f"(Phòng: {self._department})")
        for d in details:
            print("    " + d)
        print(f"    Thưởng tháng : {money(self._monthly_bonus)}")
        print(f"    Thu nhập     : {money(self.calculate_gross_pay())}")


#  Lớp dẫn xuất
class SalariedEmployee(Employee):
    def __init__(self, employee_id, full_name, department, monthly_salary, responsibility_allowance):
        super().__init__(employee_id, full_name, department)       # ủy quyền kiểm tra cho lớp cha
        self._monthly_salary = number(monthly_salary, "Lương tháng")
        self._allowance = number(responsibility_allowance, "Phụ cấp trách nhiệm")

    @classmethod
    def basic(cls, employee_id, full_name, monthly_salary):        # constructor rút gọn
        return cls(employee_id, full_name, DEFAULT_DEPT, monthly_salary, 0.0)

    def calculate_gross_pay(self) -> float:
        return self._monthly_salary + self._allowance + self.monthly_bonus

    def get_employee_type(self) -> str:
        return "SalariedEmployee"

    def display_payroll_info(self) -> None:
        self._show(f"Lương tháng  : {money(self._monthly_salary)}",
                   f"Phụ cấp TN   : {money(self._allowance)}")


class HourlyEmployee(Employee):
    STANDARD_HOURS, OVERTIME_FACTOR, MAX_HOURS = 160.0, 1.5, 250.0

    def __init__(self, employee_id, full_name, department, hourly_rate, worked_hours):
        super().__init__(employee_id, full_name, department)
        self._hourly_rate = number(hourly_rate, "Đơn giá giờ")
        self._worked_hours = number(worked_hours, "Số giờ làm", 0, self.MAX_HOURS)

    @classmethod
    def basic(cls, employee_id, full_name, hourly_rate):           # constructor rút gọn
        return cls(employee_id, full_name, DEFAULT_DEPT, hourly_rate, 0.0)

    @property
    def overtime_hours(self) -> float:   # tính từ trạng thái hiện có, không lưu riêng
        return max(0.0, self._worked_hours - self.STANDARD_HOURS)

    def calculate_gross_pay(self) -> float:
        regular = min(self._worked_hours, self.STANDARD_HOURS)
        base = (regular + self.overtime_hours * self.OVERTIME_FACTOR) * self._hourly_rate
        return base + self.monthly_bonus

    def get_employee_type(self) -> str:
        return "HourlyEmployee"

    def display_payroll_info(self) -> None:
        self._show(f"Đơn giá giờ  : {money(self._hourly_rate)}",
                   f"Số giờ làm   : {self._worked_hours:g} (vượt 160: {self.overtime_hours:g})")


class SalesEmployee(Employee):
    MAX_COMMISSION = 0.3

    def __init__(self, employee_id, full_name, department, base_salary, sales_revenue, commission_rate):
        super().__init__(employee_id, full_name, department)
        self._base_salary = number(base_salary, "Lương cơ bản")
        self._sales_revenue = number(sales_revenue, "Doanh số")
        self._commission_rate = number(commission_rate, "Tỷ lệ hoa hồng", 0, self.MAX_COMMISSION)

    @classmethod
    def basic(cls, employee_id, full_name, base_salary):           # constructor rút gọn
        return cls(employee_id, full_name, DEFAULT_DEPT, base_salary, 0.0, 0.0)

    def update_sales_revenue(self, new_revenue: float) -> None:    # cập nhật có kiểm soát
        self._sales_revenue = number(new_revenue, "Doanh số")

    def calculate_gross_pay(self) -> float:
        return self._base_salary + self._sales_revenue * self._commission_rate + self.monthly_bonus

    def get_employee_type(self) -> str:
        return "SalesEmployee"

    def display_payroll_info(self) -> None:
        self._show(f"Lương cơ bản : {money(self._base_salary)}",
                   f"Doanh số     : {money(self._sales_revenue)} x {self._commission_rate:.1%}")


#  Bảng lương
class Payroll:
    """Quan hệ KẾT TẬP với Employee (1 — 0..*), KHÔNG kế thừa (Payroll không phải Employee).
    Lưu dict {mã: Employee}: là tham chiếu tới đối tượng thật nên không mất hành vi lớp
    dẫn xuất (A.8.3); tra trùng mã O(1). Không if/else theo loại: mọi phép tính gọi
    calculate_gross_pay() qua kiểu chung Employee."""

    def __init__(self, period: str):
        parts = text(period, "Kỳ lương").split("-")
        if not (len(parts) == 2 and len(parts[0]) == 4 and len(parts[1]) == 2
                and all(p.isdigit() for p in parts) and 1 <= int(parts[1]) <= 12):
            raise ValueError("Kỳ lương phải có dạng YYYY-MM")
        self._period = period.strip()
        self._employees: Dict[str, Employee] = {}

    period = property(lambda self: self._period)

    def __len__(self) -> int:
        return len(self._employees)

    def add_employee(self, employee: Employee) -> bool:
        """False nếu trùng mã; TypeError nếu không phải Employee."""
        if not isinstance(employee, Employee):
            raise TypeError("Chỉ được thêm đối tượng kiểu Employee")
        if employee.employee_id in self._employees:
            return False
        self._employees[employee.employee_id] = employee
        return True

    def find_employee(self, employee_id: str) -> Optional[Employee]:
        if not isinstance(employee_id, str):
            return None
        return self._employees.get(employee_id.strip())

    def calculate_total_payroll(self) -> float:
        return sum(e.calculate_gross_pay() for e in self._employees.values())

    def calculate_payroll_by_department(self, department: str) -> float:
        return sum(e.calculate_gross_pay() for e in self._employees.values()
                   if e.department == department)

    def find_highest_paid_employee(self) -> Optional[Employee]:
        return max(self._employees.values(), key=lambda e: e.calculate_gross_pay(), default=None)

    def display_payroll(self) -> None:
        print(f"===== BẢNG LƯƠNG KỲ {self._period} =====")
        if not self._employees:
            print("(Bảng lương chưa có nhân sự nào)")
        for e in self._employees.values():
            e.display_payroll_info()          # gọi đa hình
        print(f"TỔNG BẢNG LƯƠNG: {money(self.calculate_total_payroll())}")
        top = self.find_highest_paid_employee()
        if top:
            print(f"Cao nhất: {top.full_name} ({top.employee_id}) - {money(top.calculate_gross_pay())}")


#  Giao diện
def read_text(prompt: str) -> str:
    return input(prompt).strip()


def read_number(prompt: str) -> float:
    """Nhập số (dùng dấu phẩy hoặc chấm cho phần thập phân, không dùng dấu phân cách hàng nghìn)."""
    while True:
        raw = input(prompt).strip().replace(" ", "").replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            print("  Vui lòng nhập một số hợp lệ.")


def read_department() -> str:
    return read_text(f"Phòng ban (Enter = {DEFAULT_DEPT}): ") or DEFAULT_DEPT


def add_salaried(payroll: Payroll) -> None:
    emp = SalariedEmployee(read_text("Mã nhân sự: "), read_text("Họ tên: "), read_department(),
                           read_number("Lương tháng: "), read_number("Phụ cấp trách nhiệm: "))
    print("Đã thêm vào bảng lương." if payroll.add_employee(emp)
          else "Không thêm được: mã nhân sự đã tồn tại.")


def add_hourly(payroll: Payroll) -> None:
    emp = HourlyEmployee(read_text("Mã nhân sự: "), read_text("Họ tên: "), read_department(),
                         read_number("Đơn giá giờ: "), read_number("Số giờ làm (0 - 250): "))
    print("Đã thêm vào bảng lương." if payroll.add_employee(emp)
          else "Không thêm được: mã nhân sự đã tồn tại.")


def add_sales(payroll: Payroll) -> None:
    emp = SalesEmployee(read_text("Mã nhân sự: "), read_text("Họ tên: "), read_department(),
                        read_number("Lương cơ bản: "), read_number("Doanh số: "),
                        read_number("Tỷ lệ hoa hồng (0 - 0,3; ví dụ 0,05): "))
    print("Đã thêm vào bảng lương." if payroll.add_employee(emp)
          else "Không thêm được: mã nhân sự đã tồn tại.")


def ask_employee(payroll: Payroll) -> Optional[Employee]:
    emp = payroll.find_employee(read_text("Nhập mã nhân sự: "))
    if emp is None:
        print("Không tìm thấy nhân sự có mã này.")
    return emp


def add_bonus(payroll: Payroll) -> None:
    emp = ask_employee(payroll)
    if emp is None:
        return
    print("  1. Thưởng cố định           addBonus(amount)")
    print("  2. Thưởng cố định + lý do   addBonus(amount, reason)")
    print("  3. Thưởng theo tỷ lệ        addBonus(rate, referenceAmount, reason)")
    choice = read_text("Chọn kiểu thưởng: ")
    if choice == "1":
        emp.add_bonus(read_number("Số tiền thưởng: "))
    elif choice == "2":
        emp.add_bonus(read_number("Số tiền thưởng: "), read_text("Lý do: "))
    elif choice == "3":
        emp.add_bonus(read_number("Tỷ lệ thưởng (0 - 0,5; ví dụ 0,02): "),
                      read_number("Giá trị tham chiếu: "), read_text("Lý do: "))
    else:
        print("Lựa chọn không hợp lệ.")
        return
    print(f"Đã ghi nhận thưởng. Tổng thưởng tháng của {emp.full_name}: {money(emp.monthly_bonus)}")


def reset_bonus(payroll: Payroll) -> None:
    emp = ask_employee(payroll)
    if emp is not None:
        emp.reset_bonus()
        print(f"Đã đặt lại thưởng của {emp.full_name} về 0.")


def update_revenue(payroll: Payroll) -> None:
    emp = ask_employee(payroll)
    if emp is None:
        return
    if not isinstance(emp, SalesEmployee):
        print("Chỉ cập nhật được doanh số cho nhân viên kinh doanh.")
        return
    emp.update_sales_revenue(read_number("Doanh số mới: "))
    print("Đã cập nhật doanh số.")


def find_employee(payroll: Payroll) -> None:
    emp = ask_employee(payroll)
    if emp is not None:
        emp.display_payroll_info()


def show_total(payroll: Payroll) -> None:
    print(f"Tổng bảng lương: {money(payroll.calculate_total_payroll())}")


def show_by_department(payroll: Payroll) -> None:
    dept = read_text("Tên phòng ban: ")
    print(f"Tổng lương phòng {dept}: {money(payroll.calculate_payroll_by_department(dept))}")


def show_highest(payroll: Payroll) -> None:
    top = payroll.find_highest_paid_employee()
    if top is None:
        print("Bảng lương chưa có nhân sự nào.")
    else:
        print(f"Cao nhất: {top.full_name} ({top.employee_id}) - {money(top.calculate_gross_pay())}")


MENU = [
    ("Thêm nhân viên lương cố định", add_salaried),
    ("Thêm nhân viên theo giờ", add_hourly),
    ("Thêm nhân viên kinh doanh", add_sales),
    ("Thêm thưởng cho nhân sự", add_bonus),
    ("Đặt lại thưởng (kỳ lương mới)", reset_bonus),
    ("Cập nhật doanh số nhân viên kinh doanh", update_revenue),
    ("Tìm nhân sự theo mã", find_employee),
    ("Hiển thị bảng lương", lambda pr: pr.display_payroll()),
    ("Tính tổng bảng lương", show_total),
    ("Tính tổng lương theo phòng ban", show_by_department),
    ("Tìm người có thu nhập cao nhất", show_highest),
]


def load_sample_data(payroll: Payroll) -> None:
    """Nạp sẵn dữ liệu mẫu của đề (mục C)."""
    e1 = SalariedEmployee("E001", "Nguyễn Minh An", "Đào tạo", 15_000_000, 2_000_000)
    e1.add_bonus(1_000_000)                                    # addBonus(amount)
    e2 = HourlyEmployee("E002", "Trần Thu Bình", "Hỗ trợ", 100_000, 150)
    e2.add_bonus(500_000, "Thưởng chuyên cần")                 # addBonus(amount, reason)
    e3 = HourlyEmployee("E003", "Lê Hoàng Chi", "Hỗ trợ", 100_000, 170)
    e4 = SalesEmployee("E004", "Phạm Quốc Dũng", "Kinh doanh", 8_000_000, 200_000_000, 0.05)
    e4.add_bonus(0.02, 50_000_000, "Thưởng doanh số")          # addBonus(rate, referenceAmount, reason)
    for e in (e1, e2, e3, e4):
        payroll.add_employee(e)


def main() -> None:
    payroll = Payroll("2026-10")
    load_sample_data(payroll)

    while True:
        print(f"\n===== QUẢN LÝ LƯƠNG KỲ {payroll.period} =====")
        for i, (label, _) in enumerate(MENU, 1):
            print(f"{i:>2}. {label}")
        print(" 0. Thoát")
        choice = read_text("Chọn chức năng: ")
        if choice == "0":
            print("Kết thúc chương trình.")
            break
        if not (choice.isdigit() and 1 <= int(choice) <= len(MENU)):
            print("Lựa chọn không hợp lệ.")
            continue
        try:
            MENU[int(choice) - 1][1](payroll)
        except (TypeError, ValueError) as ex:      # dữ liệu sai: báo lỗi, không làm đổi trạng thái
            print(f"  Lỗi: {ex}")


if __name__ == "__main__":
    main()8

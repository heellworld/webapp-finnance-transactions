from wtforms import StringField, BooleanField, DecimalField, DateField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange
from flask_wtf import FlaskForm
from models import User
from datetime import datetime, timedelta
from decimal import Decimal

class TransactionForm(FlaskForm):
    lender_account = StringField('Lender Account', validators=[
        DataRequired(message='Số tài khoản người cho vay không được để trống'),
        Length(min=10, max=20, message='Số tài khoản người cho vay không hợp lệ')
    ])
    
    borrower_account = StringField('Borrower Account', validators=[
        DataRequired(message='Số tài khoản người vay không được để trống'), 
        Length(min=10, max=20, message='Số tài khoản người vay không hợp lệ')
    ])
    
    amount = DecimalField('Amount', validators=[
        DataRequired(message='Số tiền không được để trống'),
        NumberRange(min=100, message='Số tiền tối thiểu là 100 VND')
    ])
    
    due_date = DateField('Due Date', validators=[
        DataRequired(message='Ngày đến hạn không được để trống')
    ])

        # Thêm checkbox xác nhận
    confirm_borrow = BooleanField('Xác nhận cho vay thêm')


    def validate_due_date(self, field):
        min_date = datetime.now().date() + timedelta(days=1)
        max_date = datetime.now().date() + timedelta(days=365)
        
        if field.data <= datetime.now().date():
            raise ValidationError('Ngày đến hạn phải lớn hơn ngày hiện tại')
        if field.data < min_date:
            raise ValidationError('Ngày đến hạn phải cách ngày hiện tại ít nhất 1 ngày')
        if field.data > max_date:
            raise ValidationError('Thời hạn vay tối đa là 1 năm')

    def validate_borrower_account(self, field):
        if field.data == self.lender_account.data:
            raise ValidationError('Tài khoản người vay không thể giống tài khoản người cho vay')

        borrower = User.query.filter_by(bank_account=field.data).first()
        if not borrower:
            raise ValidationError('Không tìm thấy tài khoản người vay')


    def validate_lender_account(self, field):
        lender = User.query.filter_by(bank_account=field.data).first()
        if not lender:
            raise ValidationError('Không tìm thấy tài khoản người cho vay')
        
        # Kiểm tra số dư tài khoản
        if lender.bank_balance < Decimal(str(self.amount.data)):
            raise ValidationError('Số dư tài khoản không đủ để thực hiện giao dịch')
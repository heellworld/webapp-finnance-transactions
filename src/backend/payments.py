from wtforms import StringField, DecimalField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange
from flask import current_app
from flask_wtf import FlaskForm
from models import User, Loan, LoanStatus
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal, InvalidOperation

class PaymentForm(FlaskForm):
    borrower_account = StringField('Borrower Account', validators=[
        DataRequired(message='Số tài khoản người vay không được để trống'),
        Length(min=10, max=20, message='Số tài khoản người vay không hợp lệ')
    ])

    lender_account = StringField('Lender Account', validators=[
        DataRequired(message='Số tài khoản người cho vay không được để trống'),
        Length(min=10, max=20, message='Số tài khoản người cho vay không hợp lệ')
    ])
    
    amount = DecimalField('Amount', validators=[
        DataRequired(message='Số tiền không được để trống'),
        NumberRange(min=100, message='Số tiền tối thiểu là 100 VND')
    ])

    def validate(self, **kwargs):
        if not super().validate():
            return False

        try:
            # Validate that the borrower and lender accounts exist
            borrower = User.query.filter_by(bank_account=self.borrower_account.data).first()
            lender = User.query.filter_by(bank_account=self.lender_account.data).first()

            if not borrower:
                self.borrower_account.errors.append('Tài khoản người vay không tồn tại')
                return False

            if not lender:
                self.lender_account.errors.append('Tài khoản người cho vay không tồn tại')
                return False

            # Validate loan exists
            loan = Loan.query.filter(
                Loan.borrower_id == borrower.id,
                Loan.lender_id == lender.id,
                Loan.status == LoanStatus.ACTIVE
            ).first()

            if not loan:
                self.lender_account.errors.append('Không tìm thấy khoản vay phù hợp')
                return False

            # Validate amount
            try:
                amount = Decimal(str(self.amount.data))
                if amount <= 0:
                    self.amount.errors.append('Số tiền phải lớn hơn 0')
                    return False
                
                if amount > loan.remaining_amount:
                    self.amount.errors.append('Số tiền thanh toán không thể lớn hơn số tiền còn nợ')
                    return False
                
                if amount > borrower.bank_balance:
                    self.amount.errors.append('Số dư tài khoản không đủ để thực hiện thanh toán')
                    return False
                    
            except (ValueError, TypeError, InvalidOperation):
                self.amount.errors.append('Số tiền không hợp lệ')
                return False

            return True

        except SQLAlchemyError as e:
            # Log the error
            current_app.logger.error(f"Database error in form validation: {str(e)}")
            raise ValidationError('Lỗi hệ thống, vui lòng thử lại sau')
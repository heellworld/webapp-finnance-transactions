import os
import sys
sys.path.append(os.path.abspath(".."))
from datetime import datetime
import enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Integer, String, DateTime, ForeignKey, Enum, func, Numeric, Column
from sqlalchemy.orm import relationship
from src import db, app

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

class LoanStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    OVERDUE = "overdue"

class User(BaseModel, UserMixin):
    __tablename__ = 'users'

    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    bank_account = Column(String(50), unique=True, nullable=False)
    bank_balance = Column(Numeric(15, 2), default=0.0)
    created_at = Column(DateTime, default=func.now())

    loans_given = relationship(
        'Loan',
        foreign_keys='Loan.lender_id',
        backref='lender',
        lazy=True
    )
    loans_received = relationship(
        'Loan',
        foreign_keys='Loan.borrower_id',
        backref='borrower',
        lazy=True
    )

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __str__(self):
        return self.name

class Loan(BaseModel):
    __tablename__ = 'loans'

    lender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    borrower_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(Enum(LoanStatus), default=LoanStatus.PENDING)
    loan_created_at = Column(DateTime, default=func.now())

    payments = relationship('Payment', backref='loan', lazy=True) 
    
    def calculate_remaining_amount(self):
        paid_amount = sum(payment.amount for payment in self.payments if payment.status == 'success')
        return self.amount - paid_amount

    def update_status(self):
        if datetime.now() > self.due_date and self.remaining_amount > 0:
            self.status = LoanStatus.OVERDUE
        elif self.remaining_amount <= 0:
            self.status = LoanStatus.COMPLETED

    def __str__(self):
        return ', '.join(filter(None, [self.amount, self.remaining_amount, self.due_date, self.status, self.loan_created_at]))

class Payment(BaseModel):
    __tablename__ = 'payments'

    loan_id = Column(Integer, ForeignKey('loans.id'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String(20), default='pending')
    transaction_id = Column(String(100), unique=True, nullable=False)
    payment_created_at = Column(DateTime, default=func.now())

    def __str__(self):
        return ', '.join(filter(None, [self.amount, self.status, self.transaction_id, self.payment_created_at]))


# Event listener để cập nhật trạng thái khoản vay sau khi thanh toán
@db.event.listens_for(Payment, 'after_insert')
def update_loan_after_payment(mapper, connection, target):
    with db.session.begin(subtransactions=True):
        loan = db.session.get(Loan, target.loan_id)
        if loan and target.status == 'success':
            loan.remaining_amount -= target.amount
            if loan.remaining_amount <= 0:
                loan.status = LoanStatus.COMPLETED
            db.session.add(loan)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
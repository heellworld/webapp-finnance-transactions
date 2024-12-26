from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email, Length, ValidationError
import re
from flask_wtf import FlaskForm
from models import User

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Tên phải có độ dài từ 2 đến 100 ký tự')
    ])

    email = EmailField('Email', validators=[
        DataRequired(),
        Email(message='Email không hợp lệ')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Mật khẩu phải có ít nhất 8 ký tự')
    ])
    
    bank_account = StringField('Bank Account', validators=[
        DataRequired(),
        Length(min=10, max=20, message='Số tài khoản không hợp lệ')
    ])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email đã được đăng ký')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Tên đăng nhập đã tồn tại')

    def validate_bank_account(self, field):
        if not re.match(r'^\d{10,20}$', field.data):
            raise ValidationError('Số tài khoản phải chứa 10-20 chữ số')
        if User.query.filter_by(bank_account=field.data).first():
            raise ValidationError('Số tài khoản đã được đăng ký')
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from flask_wtf import FlaskForm
from models import User

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[
        DataRequired(message='Email không được để trống'),
        Email(message='Email không hợp lệ')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Mật khẩu không được để trống'),
        Length(min=8, message='Mật khẩu phải có ít nhất 8 ký tự')
    ])

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if not user:
            print(f"Email không tồn tại: {field.data}")
            raise ValidationError('Email chưa được đăng ký')
        if not user.is_active:
            raise ValidationError('Tài khoản đã bị khóa hoặc không hoạt động')
        self.user = user

    def validate_password(self, field):
        if not hasattr(self, 'user'):
            return
        if not self.user.check_password(field.data):
            print(f"Mật khẩu không khớp cho email: {self.email.data}")
            raise ValidationError('Mật khẩu không hợp lệ')

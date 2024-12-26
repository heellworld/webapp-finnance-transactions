import os
import sys
sys.path.append(os.path.abspath(".."))
from src import db, app, mail
from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from backend import register, login, transactions, payments
from models import User, Loan, LoanStatus, Payment
from urllib.parse import urlparse, urljoin
from flask_login import login_user, LoginManager, login_required, current_user
from decimal import Decimal, InvalidOperation
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from flask_mail import Message

# Khởi tạo LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Thêm int() để đảm bảo user_id là số

@app.route('/')
def home():
    return render_template('index.html')

# Đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('transactions'))
        
    form = register.RegistrationForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            new_user = User(
                name=form.name.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
                bank_account=form.bank_account.data,
                bank_balance=Decimal('1000000')  # Sử dụng Decimal cho độ chính xác
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Đăng ký tài khoản thành công!', 'success')
            return redirect(url_for('login'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Có lỗi xảy ra trong quá trình đăng ký. Vui lòng thử lại!', 'error')
            app.logger.error(f"Registration error: {str(e)}")
    
    return render_template('register.html', form=form)

@app.route('/forgetpass', methods=['GET', 'POST'])
def forgetpass():
    if request.method == 'POST':
        msg = Message(
            'Thông báo thanh toán khoản vay',
            sender="ctvayno@gmail.com",
            recipients=["tuanleanh4112003@gmail.com"]
        )
        msg.body = f"""
        Trân trọng,
        Hệ thống quản lý khoản vay
        Tài khoản ... muốn tìm lại mật khẩu đã quên
        """
        mail.send(msg)
        return 'send email'
    return render_template('forgetpass.html')

# Đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('transactions'))
        
    form = login.LoginForm()

    if form.validate_on_submit():
        login_user(form.user)
        flash('Đăng nhập thành công!', 'success')

        next_page = request.args.get('next')
        if not next_page or not is_safe_url(next_page):
            next_page = url_for('transactions')
        return redirect(next_page)

    return render_template('login.html', form=form)

# Thực hiện giao dịch
@app.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    form = transactions.TransactionForm()

    if request.method == 'POST' and form.validate_on_submit():
        if current_user.bank_account != form.lender_account.data:
            flash('Bạn chỉ có thể tạo giao dịch với tài khoản của mình', 'error')
            return redirect(url_for('transactions'))
        
        try:
            lender = User.query.filter_by(bank_account=form.lender_account.data).first()
            borrower = User.query.filter_by(bank_account=form.borrower_account.data).first()
            
            if not lender or not borrower:
                flash('Không tìm thấy thông tin tài khoản', 'error')
                return redirect(url_for('transactions'))
            
            amount = Decimal(str(form.amount.data))
            
            if lender.bank_balance < amount:
                flash('Số dư tài khoản không đủ để thực hiện giao dịch', 'error')
                return redirect(url_for('transactions'))
            
            # Sử dụng transaction để đảm bảo tính nhất quán
            db.session.begin_nested()
            
            loan = Loan(
                lender_id=lender.id,
                borrower_id=borrower.id,
                amount=amount,
                remaining_amount=amount,
                due_date=form.due_date.data,
                status=LoanStatus.ACTIVE,
                loan_created_at=datetime.now()
            )
            
            lender.bank_balance -= amount
            borrower.bank_balance += amount
            
            db.session.add(loan)
            db.session.commit()  # Commit lần đầu
            
            try:
                # Tạo email thông báo cho người cho vay
                msg_lender = Message(
                    'Thông báo thanh toán khoản vay',
                    sender='ctvayno@gmail.com',
                    recipients=[lender.email]
                )
                msg_lender.body = f"""
                Xin chào {lender.name},
                
                Bạn vừa thanh toán khoản vay với thông tin sau:
                Số tiền: {amount:,.0f} VND
                Số dư tài khoản hiện tại của bạn: {lender.bank_balance:,.0f} VND
                Ngày thanh toán: {loan.loan_created_at.strftime('%Y-%m-%d %H:%M:%S')}
                Người nhận: {borrower.name}
                
                Trân trọng,
                Hệ thống quản lý khoản vay (Nhóm 2)
                """
                # Tạo email thông báo cho người vay
                msg_borrower = Message(
                    'Thông báo khoản vay',
                    sender='ctvayno@gmail.com',
                    recipients=[borrower.email]
                )
                msg_borrower.body = f"""
                Xin chào {borrower.name},
                
                Bạn vừa nhận được khoản vay với thông tin sau:
                Số tiền: {amount:,.0f} VND
                Số dư tài khoản hiện tại của bạn: {borrower.bank_balance:,.0f} VND
                Ngày nhận tiền: {loan.loan_created_at.strftime('%Y-%m-%d %H:%M:%S')}
                Người cho vay: {lender.name}
                
                Trân trọng,
                Hệ thống quản lý khoản vay (Nhóm 2)
                """
                mail.send(msg_lender)
                mail.send(msg_borrower)
                flash('Thanh toán khoản vay thành công!', 'success')
            except Exception as e:
                app.logger.error(f"Email error: {str(e)}")
                flash('Thanh toán thành công nhưng không gửi được email thông báo.', 'warning')
            
            return redirect(url_for('transactions'))

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback nếu có lỗi SQLAlchemy
            flash('Có lỗi xảy ra khi thực hiện giao dịch.', 'error')
            app.logger.error(f"Transaction error: {str(e)}")
            return redirect(url_for('transactions'))
    
    loans_given = Loan.query.filter_by(lender_id=current_user.id).order_by(Loan.loan_created_at.desc()).all()
    loans_received = Loan.query.filter_by(borrower_id=current_user.id).order_by(Loan.loan_created_at.desc()).all()

    return render_template(
        'transactions.html',
        form=form,
        loans_given=loans_given,
        loans_received=loans_received,
        user=current_user
    )

# Thanh toán khoản vay
@app.route('/payments', methods=['GET', 'POST'])
@login_required
def payments():
    form = payments.PaymentForm()

    try:
        if request.method == 'GET':
            active_loans = Loan.query.filter(
                ((Loan.borrower_id == current_user.id) | 
                 (Loan.lender_id == current_user.id)) &
                (Loan.status == LoanStatus.ACTIVE)
            ).order_by(Loan.due_date.asc()).all()
            
            return render_template('payments.html', form=form, active_loans=active_loans)

        if form.validate_on_submit():
            # Kiểm tra tài khoản thanh toán
            if not current_user.bank_account:
                flash('Bạn chưa liên kết tài khoản ngân hàng.', 'error')
                return redirect(url_for('payments'))

            if current_user.bank_account != form.borrower_account.data:
                flash('Bạn chỉ có thể thanh toán bằng tài khoản ngân hàng của mình.', 'error')
                return redirect(url_for('payments'))

            # Validate số tiền trước khi bắt đầu transaction
            try:
                amount = Decimal(str(form.amount.data))
                if amount <= 0:
                    flash('Số tiền thanh toán phải lớn hơn 0.', 'error')
                    return redirect(url_for('payments'))
            except (InvalidOperation, ValueError) as e:
                app.logger.error(f"Lỗi chuyển đổi số tiền: {str(e)}", extra={
                    'amount_input': form.amount.data
                })
                flash('Số tiền không hợp lệ.', 'error')
                return redirect(url_for('payments'))

            # Tìm khoản vay trước khi bắt đầu transaction
            loan = Loan.query.join(User, Loan.lender_id == User.id).filter(
                User.bank_account == form.lender_account.data,
                Loan.borrower_id == current_user.id,
                Loan.status == LoanStatus.ACTIVE
            ).first()

            if not loan:
                flash('Không tìm thấy khoản vay phù hợp.', 'error')
                return redirect(url_for('payments'))

            # Kiểm tra số tiền thanh toán với số tiền còn lại
            if amount > loan.remaining_amount:
                flash('Số tiền thanh toán không thể lớn hơn số tiền còn nợ.', 'error')
                return redirect(url_for('payments'))

            # Bắt đầu transaction
            with db.session.begin_nested():
                # Lock các bản ghi theo thứ tự để tránh deadlock
                loan = Loan.query.filter_by(id=loan.id).with_for_update().first()
                borrower = User.query.filter_by(id=current_user.id).with_for_update().first()
                lender = User.query.filter_by(id=loan.lender_id).with_for_update().first()

                if not all([loan, borrower, lender]):
                    raise ValueError("Không thể load đầy đủ thông tin giao dịch")

                # Kiểm tra lại số dư sau khi lock
                if borrower.bank_balance < amount:
                    flash('Số dư tài khoản không đủ để thực hiện giao dịch.', 'error')
                    return redirect(url_for('payments'))

                # Tạo bản ghi thanh toán
                payment = Payment(
                    loan_id=loan.id,
                    amount=amount,
                    payment_created_at=datetime.now()
                )
                db.session.add(payment)

                # Cập nhật số dư
                borrower.bank_balance -= amount
                lender.bank_balance += amount

                # Cập nhật khoản vay
                loan.remaining_amount -= amount
                if loan.remaining_amount == 0:
                    loan.status = LoanStatus.COMPLETED
                    loan.completed_at = datetime.now()

                # Commit transaction chính
                db.session.commit()

                # Gửi email thông báo (ngoài transaction)
                try:
                    # Tạo email thông báo cho người cho vay
                    msg_lender = Message(
                        'Thông báo thanh toán khoản vay',
                        sender='ctvayno@gmail.com',
                        recipients=[lender.email]
                    )
                    msg_lender.body = f"""
                    Xin chào {lender.name},
                    
                    Bạn vừa thanh toán khoản vay với thông tin sau:
                    Số tiền: {amount:,.0f} VND
                    Số dư tài khoản hiện tại của bạn: {lender.bank_balance:,.0f} VND
                    Ngày thanh toán: {loan.loan_created_at.strftime('%Y-%m-%d %H:%M:%S')}
                    Người nhận: {borrower.name}
                    
                    Trân trọng,
                    Hệ thống quản lý khoản vay (Nhóm 2)
                    """
                    # Tạo email thông báo cho người vay
                    msg_borrower = Message(
                        'Thông báo khoản vay',
                        sender='ctvayno@gmail.com',
                        recipients=[borrower.email]
                    )
                    msg_borrower.body = f"""
                    Xin chào {borrower.name},
                    
                    Bạn vừa nhận được khoản vay với thông tin sau:
                    Số tiền: {amount:,.0f} VND
                    Số dư tài khoản hiện tại của bạn: {borrower.bank_balance:,.0f} VND
                    Ngày nhận tiền: {loan.loan_created_at.strftime('%Y-%m-%d %H:%M:%S')}
                    Người cho vay: {lender.name}
                    
                    Trân trọng,
                    Hệ thống quản lý khoản vay (Nhóm 2)
                    """
                    mail.send(msg_lender)
                    mail.send(msg_borrower)
                    flash('Thanh toán khoản vay thành công!', 'success')
                except Exception as e:
                    app.logger.error(f"Email error: {str(e)}")
                    flash('Thanh toán thành công nhưng không gửi được email thông báo.', 'warning')
                
                return redirect(url_for('payments'))

    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Lỗi transaction SQL: {str(e)}", extra={
            'user_id': current_user.id,
            'loan_id': loan.id if 'loan' in locals() else None,
            'amount': str(amount),
            'error_type': type(e).__name__,
            'error': str(e)
        })
        flash('Có lỗi xảy ra khi thực hiện thanh toán. Vui lòng thử lại.', 'error')
        return redirect(url_for('payments'))

    return render_template('payments.html', form=form)


if __name__ == '__main__':
    from admin import *
    app.run(debug=True)
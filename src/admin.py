import os
import sys
sys.path.append(os.path.abspath(".."))
from src import db, app
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import User, Loan, Payment

admin = Admin(app, name='Administrator', template_mode='bootstrap4')

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Loan, db.session))
admin.add_view(ModelView(Payment, db.session))

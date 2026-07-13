from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_caching import Cache

import config
from models import db, mail, Role, Branch, User
from werkzeug.security import generate_password_hash

jwt = JWTManager()
cache = Cache()

DEFAULT_BRANCHES = [
    'Computer Science',
    'Information Technology',
    'Electronics & Communication',
    'Electrical Engineering',
    'Mechanical Engineering',
    'Civil Engineering',
    'Chemical Engineering',
    'Biotechnology',
]


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": config.CORS_ORIGINS}}, supports_credentials=True)

    from services.auth import auth_bp
    from services.admin import admin_bp
    from services.company import company_bp
    from services.student import student_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(company_bp, url_prefix='/api/company')
    app.register_blueprint(student_bp, url_prefix='/api/student')

    register_cli(app)
    return app


def register_cli(app):
    @app.cli.command('init-db')
    def init_db():
        db.create_all()
        seed_branches()
        seed_admin()
        print('Database initialized.')


def seed_branches():
    for name in DEFAULT_BRANCHES:
        if not Branch.query.filter_by(name=name).first():
            db.session.add(Branch(name=name))
    db.session.commit()


def seed_admin():
    if User.query.filter_by(role=Role.ADMIN).first():
        return
    admin = User(
        name='Institute Admin',
        role=Role.ADMIN,
        email=config.ADMIN_EMAIL,
        password=generate_password_hash(config.ADMIN_PASSWORD),
        is_active=True,
    )
    db.session.add(admin)
    db.session.commit()


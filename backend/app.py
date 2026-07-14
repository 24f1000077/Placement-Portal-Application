from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_caching import Cache

import config
from models import db, mail, Role, Branch, User
from werkzeug.security import generate_password_hash

# Shared extension instances, initialized against the app inside create_app().
jwt = JWTManager()
cache = Cache()

# Branches seeded into the database on first startup.
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
    # Builds and configures the Flask app instance.
    app = Flask(__name__)
    app.config.from_object(config)
    app.config["DEBUG"] = True

    # Binds the database, mail, JWT, and cache extensions to this app.
    db.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    # Allows the frontend origin to call the /api/* routes with credentials.
    CORS(app, resources={r"/api/*": {"origins": config.CORS_ORIGINS}}, supports_credentials=True)

    # Blueprint imports are deferred until after extension init to avoid circular imports.
    from services.auth import auth_bp
    from services.admin import admin_bp
    from services.company import company_bp
    from services.student import student_bp

    # Mounts each role's routes under its own /api prefix.
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(company_bp, url_prefix='/api/company')
    app.register_blueprint(student_bp, url_prefix='/api/student')

    # Creates any missing tables and seeds branches/admin on every app start.
    with app.app_context():
        db.create_all()
        seed_branches()
        seed_admin()

    return app


def seed_branches():
    # Inserts any branch from DEFAULT_BRANCHES that doesn't already exist.
    for name in DEFAULT_BRANCHES:
        if not Branch.query.filter_by(name=name).first():
            db.session.add(Branch(name=name))
    db.session.commit()


def seed_admin():
    # No-ops if an admin account already exists.
    if User.query.filter_by(role=Role.ADMIN).first():
        return
    # Creates the single admin account from the configured email/password.
    admin = User(
        name='Institute Admin',
        role=Role.ADMIN,
        email=config.ADMIN_EMAIL,
        password=generate_password_hash(config.ADMIN_PASSWORD),
        is_active=True,
    )
    db.session.add(admin)
    db.session.commit()

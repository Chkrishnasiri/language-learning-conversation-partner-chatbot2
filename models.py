from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )
    password = db.Column(
        db.String(100),
        nullable=False
    )
    xp = db.Column(
        db.Integer,
        default=0
    )
    streak = db.Column(
        db.Integer,
        default=0
    )
    selected_language = db.Column(
        db.String(50),
        default="Telugu"
    )
    last_quiz_date = db.Column(
        db.String(20),
        default=""
    )

quiz_attempted_today = db.Column(
    db.String(20),
    default=""
)
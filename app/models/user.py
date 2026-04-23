from app import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password_hash = db.Column(db.String(256), nullable=False)

    # Relationship — cascade deletes user's notes when user is deleted
    notes = db.relationship("Note", backref="user", lazy=True, cascade="all, delete-orphan")

    # Password is write-only — never expose the hash
    @property
    def password(self):
        raise AttributeError("Password is not readable.")

    def set_password(self, plain_text):
        self._password_hash = bcrypt.generate_password_hash(plain_text).decode("utf-8")

    def check_password(self, plain_text):
        return bcrypt.check_password_hash(self._password_hash, plain_text)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
        }

    def __repr__(self):
        return f"<User {self.username}>"
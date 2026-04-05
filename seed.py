from app import create_app, db
from app.models import User, Note

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    user = User(username="emman")
    user.set_password("1234")

    db.session.add(user)
    db.session.commit()

    note = Note(title="First Note", content="Hello world", user_id=user.id)
    db.session.add(note)
    db.session.commit()

    print("Seeded!")
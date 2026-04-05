from flask import Blueprint, request
from app.models import db, Note
from flask_jwt_extended import jwt_required, get_jwt_identity

note_bp = Blueprint("notes", __name__)

# GET (paginated)
@note_bp.route("/notes", methods=["GET"])
@jwt_required()
def get_notes():
    user_id = get_jwt_identity()

    page = int(request.args.get("page", 1))
    per_page = 5

    notes = Note.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page)

    return {
        "data": [
            {"id": n.id, "title": n.title, "content": n.content}
            for n in notes.items
        ],
        "page": page,
        "total_pages": notes.pages
    }


# POST
@note_bp.route("/notes", methods=["POST"])
@jwt_required()
def create_note():
    user_id = get_jwt_identity()
    data = request.json

    note = Note(
        title=data["title"],
        content=data["content"],
        user_id=user_id
    )

    db.session.add(note)
    db.session.commit()

    return {"message": "Created"}, 201


# PATCH
@note_bp.route("/notes/<int:id>", methods=["PATCH"])
@jwt_required()
def update_note(id):
    user_id = get_jwt_identity()
    note = Note.query.get_or_404(id)

    if note.user_id != user_id:
        return {"error": "Unauthorized"}, 403

    data = request.json
    note.title = data.get("title", note.title)
    note.content = data.get("content", note.content)

    db.session.commit()
    return {"message": "Updated"}


# DELETE
@note_bp.route("/notes/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_note(id):
    user_id = get_jwt_identity()
    note = Note.query.get_or_404(id)

    if note.user_id != user_id:
        return {"error": "Unauthorized"}, 403

    db.session.delete(note)
    db.session.commit()

    return {"message": "Deleted"}
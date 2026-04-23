from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Note

note_bp = Blueprint("notes", __name__)


def get_current_user_id():
    return int(get_jwt_identity())


# ── GET all notes (paginated) ──────────────────────────────────────────────────
@note_bp.route("/", methods=["GET"])
@jwt_required()
def get_notes():
    user_id = get_current_user_id()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)

    pagination = (
        Note.query
        .filter_by(user_id=user_id)
        .order_by(Note.is_pinned.desc(), Note.updated_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "notes": [note.to_dict() for note in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": per_page,
    }), 200


# ── GET single note ────────────────────────────────────────────────────────────
@note_bp.route("/<int:note_id>", methods=["GET"])
@jwt_required()
def get_note(note_id):
    user_id = get_current_user_id()
    note = Note.query.get(note_id)

    if not note:
        return jsonify({"error": "Note not found"}), 404

    # Users can only access their own notes
    if note.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify(note.to_dict()), 200


# ── POST create note ───────────────────────────────────────────────────────────
@note_bp.route("/", methods=["POST"])
@jwt_required()
def create_note():
    user_id = get_current_user_id()
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        return jsonify({"error": "title and content are required"}), 422

    note = Note(
        title=title,
        content=content,
        category=data.get("category", "general"),
        is_pinned=data.get("is_pinned", False),
        user_id=user_id,
    )

    db.session.add(note)
    db.session.commit()

    return jsonify(note.to_dict()), 201


# ── PATCH update note ──────────────────────────────────────────────────────────
@note_bp.route("/<int:note_id>", methods=["PATCH"])
@jwt_required()
def update_note(note_id):
    user_id = get_current_user_id()
    note = Note.query.get(note_id)

    if not note:
        return jsonify({"error": "Note not found"}), 404

    if note.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "title" in data:
        note.title = data["title"]
    if "content" in data:
        note.content = data["content"]
    if "category" in data:
        note.category = data["category"]
    if "is_pinned" in data:
        note.is_pinned = data["is_pinned"]

    db.session.commit()

    return jsonify(note.to_dict()), 200


# ── DELETE note ────────────────────────────────────────────────────────────────
@note_bp.route("/<int:note_id>", methods=["DELETE"])
@jwt_required()
def delete_note(note_id):
    user_id = get_current_user_id()
    note = Note.query.get(note_id)

    if not note:
        return jsonify({"error": "Note not found"}), 404

    if note.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(note)
    db.session.commit()

    return jsonify({"message": "Note deleted successfully"}), 200
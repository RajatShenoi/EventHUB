import base64
from io import BytesIO

import qrcode
from flask import current_app
from itsdangerous import BadSignature, URLSafeSerializer
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, hashed_password):
    return check_password_hash(hashed_password, password)


def make_qr_token(payload):
    serializer = URLSafeSerializer(current_app.config["SECRET_KEY"], salt="checkin")
    return serializer.dumps(payload)


def read_qr_token(token):
    serializer = URLSafeSerializer(current_app.config["SECRET_KEY"], salt="checkin")
    try:
        return serializer.loads(token)
    except BadSignature:
        return None


def qr_base64_from_token(token):
    image = qrcode.make(token)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

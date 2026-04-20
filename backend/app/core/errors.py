from flask import jsonify


class ApiError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(exc):
        return jsonify({"success": False, "message": exc.message}), exc.status_code

    @app.errorhandler(404)
    def handle_not_found(_):
        return jsonify({"success": False, "message": "Not found"}), 404

    @app.errorhandler(500)
    def handle_server_error(_):
        return jsonify({"success": False, "message": "Server error"}), 500

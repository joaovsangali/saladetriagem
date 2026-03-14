"""Custom HTTP error handlers."""
import logging

from flask import jsonify, render_template, request

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register 4xx/5xx error handlers on *app*."""

    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Requisição inválida"}), 400
        return render_template("errors/400.html"), 400

    @app.errorhandler(401)
    def unauthorized(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Não autorizado"}), 401
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Acesso negado"}), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Recurso não encontrado"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error("Erro interno: %s", error, exc_info=True)
        if request.path.startswith("/api/"):
            return jsonify({"error": "Erro interno do servidor"}), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(Exception)
    def handle_exception(exc):
        logger.error("Exceção não tratada: %s", exc, exc_info=True)
        if request.path.startswith("/api/"):
            return jsonify({"error": "Erro inesperado"}), 500
        return render_template("errors/500.html"), 500

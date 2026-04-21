"""Centralized access control for shared sessions."""

from app.models import SessionCollaborator


def can_access_session(user, session) -> tuple:
    """
    Verifica se user pode acessar session.

    Returns:
        (pode_acessar: bool, role: 'owner' | 'collaborator' | None)
    """
    # Owner sempre tem acesso total
    if session.user_id == user.id:
        return True, 'owner'

    # Verificar se é colaborador ativo
    if session.is_active and not session.is_expired:
        collab = SessionCollaborator.query.filter_by(
            session_id=session.id,
            user_id=user.id
        ).first()

        if collab:
            return True, 'collaborator'

    return False, None

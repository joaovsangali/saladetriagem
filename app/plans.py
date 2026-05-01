"""Plan definitions for Sala de Triagem monetization.

Limit fields:
  max_sessions_per_month        – None means unlimited
  max_submissions_per_session   – None means unlimited
  max_active_sessions           – simultaneous active sessions allowed
  max_session_duration_hours    – hard cap on session duration (hours)
  max_uploads_per_submission    – 0 means file uploads are not allowed
  max_photos_per_submission     – 0 means photo uploads are not allowed
"""

PLANS = {
    # -----------------------------------------------------------------------
    # FREE – basic access, no uploads, no sharing, 1 active room
    # -----------------------------------------------------------------------
    'free': {
        'name': 'Grátis',
        'max_sessions_per_month': 10,      # 10 triagens/mês
        'max_session_duration_hours': 6,   # até 6h por triagem
        'max_submissions_per_session': 15, # 15 submissões por triagem
        'can_view_photos': False,          # sem visualização de fotos/PDFs
        'can_view_pdfs': False,
        'max_photos_per_submission': 0,    # sem upload de arquivos
        'max_uploads_per_submission': 0,   # sem upload de arquivos
        'max_users': 1,
        'can_share_session': False,        # sem compartilhamento
        'can_join_shared_session': False,
        'can_create_custom_schema': False, # sem modelos personalizados
        'max_active_sessions': 1,          # 1 sala ativa por vez
    },
    # -----------------------------------------------------------------------
    # PREMIUM – media viewing, can join shares, 1 active room
    # -----------------------------------------------------------------------
    'premium': {
        'name': 'Premium',
        'max_sessions_per_month': 20,      # 20 triagens/mês
        'max_session_duration_hours': 12,  # até 12h por triagem
        'max_submissions_per_session': 50, # 50 submissões por triagem
        'can_view_photos': True,           # visualização de fotos/PDFs
        'can_view_pdfs': True,
        'max_photos_per_submission': 3,
        'max_uploads_per_submission': 3,
        'max_users': 1,
        'can_share_session': False,        # não pode criar compartilhamentos
        'can_join_shared_session': True,   # pode entrar em triagens compartilhadas
        'can_create_custom_schema': False, # sem modelos personalizados
        'max_active_sessions': 1,          # 1 sala ativa por vez
    },
    # -----------------------------------------------------------------------
    # ENTERPRISE – unlimited sessions/submissions, up to 3 active rooms
    # -----------------------------------------------------------------------
    'enterprise': {
        'name': 'Enterprise',
        'max_sessions_per_month': None,    # ilimitado
        'max_session_duration_hours': 24,  # até 24h (triagem policial); ilimitado para custom
        'max_submissions_per_session': None,  # ilimitado
        'can_view_photos': True,           # upload + visualização de fotos/PDFs
        'can_view_pdfs': True,
        'max_photos_per_submission': 6,
        'max_uploads_per_submission': 6,
        'max_users': 1,
        'can_share_session': True,         # criar e entrar em triagens compartilhadas
        'can_join_shared_session': True,
        'can_create_custom_schema': True,  # modelos personalizados
        'max_active_sessions': 3,          # até 3 salas ativas simultaneamente
    },
}

# Trial uses Premium limits
PLANS['trial'] = dict(PLANS['premium'], name='Trial Premium')

"""Plan definitions for Sala de Triagem monetization."""

PLANS = {
    'free': {
        'name': 'Grátis',
        'max_sessions_per_month': 3,
        'max_session_duration_hours': 6,
        'max_submissions_per_session': 10,
        'can_view_photos': False,
        'can_view_pdfs': False,
        'max_photos_per_submission': 3,
        'max_uploads_per_submission': 3,
        'max_users': 1,
        'can_share_session': False,
        'can_join_shared_session': False,
        'can_create_custom_schema': False,
    },
    'premium': {
        'name': 'Premium',
        'max_sessions_per_month': 20,
        'max_session_duration_hours': 12,
        'max_submissions_per_session': 20,
        'can_view_photos': True,
        'can_view_pdfs': True,
        'max_photos_per_submission': 3,
        'max_uploads_per_submission': 3,
        'max_users': 1,
        'can_share_session': False,
        'can_join_shared_session': True,
        'can_create_custom_schema': False,
    },
    'enterprise': {
        'name': 'Enterprise',
        'max_sessions_per_month': 50,
        'max_session_duration_hours': 24,
        'max_submissions_per_session': 100,
        'can_view_photos': True,
        'can_view_pdfs': True,
        'max_photos_per_submission': 6,
        'max_uploads_per_submission': 6,
        'max_users': 1,
        'can_share_session': True,
        'can_join_shared_session': True,
        'can_create_custom_schema': True,
    },
}

# Trial uses Premium limits
PLANS['trial'] = dict(PLANS['premium'], name='Trial Premium')

"""Plan definitions for Sala de Triagem monetization."""

PLANS = {
    'free': {
        'name': 'Grátis',
        'max_sessions_per_month': 5,
        'max_session_duration_hours': 6,
        'max_submissions_per_session': 10,
        'can_view_photos': False,
        'can_view_pdfs': False,
        'max_photos_per_submission': 3,
        'max_users': 1,
    },
    'premium': {
        'name': 'Premium',
        'max_sessions_per_month': 30,
        'max_session_duration_hours': 12,
        'max_submissions_per_session': 30,
        'can_view_photos': True,
        'can_view_pdfs': True,
        'max_photos_per_submission': 3,
        'max_users': 1,
    },
}

# Trial uses Premium limits
PLANS['trial'] = dict(PLANS['premium'], name='Trial Premium')

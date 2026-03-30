"""Account management forms."""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        'Senha atual',
        validators=[DataRequired(message='Informe a senha atual.')],
    )
    new_password = PasswordField(
        'Nova senha',
        validators=[
            DataRequired(message='Informe a nova senha.'),
            Length(min=8, message='A senha deve ter pelo menos 8 caracteres.'),
        ],
    )
    confirm_password = PasswordField(
        'Confirmar nova senha',
        validators=[
            DataRequired(message='Confirme a nova senha.'),
            EqualTo('new_password', message='As senhas não conferem.'),
        ],
    )
    submit = SubmitField('Alterar senha')

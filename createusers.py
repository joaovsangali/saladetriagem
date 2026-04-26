from app.models import PoliceUser
from app.extensions import db

# Criar usuário Enterprise
user = PoliceUser(
    email="enterprise@test.com",
    display_name="Usuário Enterprise",
    is_active=True,
    plan_type="enterprise"  # ← IMPORTANTE
)
user.set_password("senha123")

db.session.add(user)
db.session.commit()

print(f"✅ Usuário Enterprise criado: ID={user.id}, Email={user.email}")



from app.models import PoliceUser
from app.extensions import db

# Criar usuário Free (padrão)
user = PoliceUser(
    email="free@test.com",
    display_name="Usuário Free",
    is_active=True,
    plan_type="free"  # ← Plano Free (ou omitir, pois é o default)
)
user.set_password("senha123")

db.session.add(user)
db.session.commit()

print(f"✅ Usuário Free criado: ID={user.id}, Email={user.email}")
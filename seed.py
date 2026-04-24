from app.infrastructure.database.session import SessionLocal
from app.domain.entities.usuario import Usuario
from app.core.security import hash_password 

def create_first_user():
    db = SessionLocal()
    try:
        # Verificamos si ya existe el admin
        user_exists = db.query(Usuario).filter(Usuario.email == "admin@vallesol.com").first()
        if user_exists:
            print("ℹ️ El usuario admin@vallesol.com ya existe.")
            return

        # Usamos tu función hash_password de security.py
        password_plana = "ValleSol2026"
        hashed = hash_password(password_plana)

        new_user = Usuario(
            nombre="Admin ValleSol",
            email="admin@vallesol.com",
            password_hash=hashed,
            rol="admin",
            activo=True
        )
        
        db.add(new_user)
        db.commit()
        print("✅ ¡Usuario administrador creado con éxito!")
        print("📧 Email: admin@vallesol.com")
        print("🔑 Password: ValleSol2026")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear usuario: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_first_user()
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas import UserCreate, UserLogin, UserOut, ChangePassword
from app import crud, utils

router = APIRouter(prefix="/api/auth", tags=["auth"])

# dépendance pour la DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Register
@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    db_user = crud.create_user(db, user)
    return db_user

# Login
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if not db_user or not utils.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")
    # Ici, tu peux générer un token JWT (optionnel pour début)
    return {"message": f"Bienvenue {db_user.username}"}

# Logout
@router.post("/logout")
def logout():
    # pour JWT, supprimer le token côté client
    return {"message": "Déconnexion réussie"}

# Profil utilisateur
@router.get("/profile", response_model=UserOut)
def profile(db: Session = Depends(get_db)):
    # temporaire : retourne le premier utilisateur
    user = db.query(crud.models.User).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

# Modifier profil
@router.put("/profile/update", response_model=UserOut)
def update_profile(user_update: UserCreate, db: Session = Depends(get_db)):
    user = db.query(crud.models.User).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

# Changer mot de passe
@router.put("/profile/change-password")
def change_password(data: ChangePassword, db: Session = Depends(get_db)):
    user = db.query(crud.models.User).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    if not utils.verify_password(data.old_password, user.password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    user.password = utils.hash_password(data.new_password)
    db.commit()
    return {"message": "Mot de passe changé avec succès"}
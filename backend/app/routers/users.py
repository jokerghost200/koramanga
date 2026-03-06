from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import UserOut, UserUpdate, ChangePassword
import crud, utils

router = APIRouter(prefix="/api/users", tags=["users"])

# Dépendance DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper pour obtenir l'utilisateur actuel (simulé avec header)
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Non autorisé")
    # Pour l'instant, retourne le premier utilisateur
    # Plus tard, implémenter JWT
    user = db.query(crud.models.User).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user


# Lister tous les utilisateurs (Admin)
@router.get("/", response_model=list[UserOut])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: crud.models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return crud.get_users(db, skip, limit)


# Obtenir le profil de l'utilisateur actuel
@router.get("/me", response_model=UserOut)
def get_current_user_profile(db: Session = Depends(get_db), current_user: crud.models.User = Depends(get_current_user)):
    return current_user


# Mettre à jour le profil
@router.put("/me", response_model=UserOut)
def update_current_user(
    user_update: UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: crud.models.User = Depends(get_current_user)
):
    updated_user = crud.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(status_code=400, detail="Erreur lors de la mise à jour")
    return updated_user


# Changer le mot de passe
@router.put("/me/change-password")
def change_password(
    data: ChangePassword, 
    db: Session = Depends(get_db), 
    current_user: crud.models.User = Depends(get_current_user)
):
    if not utils.verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    
    current_user.hashed_password = utils.hash_password(data.new_password)
    db.commit()
    return {"message": "Mot de passe changé avec succès"}


# Obtenir le wallet de l'utilisateur
@router.get("/me/wallet")
def get_my_wallet(
    db: Session = Depends(get_db), 
    current_user: crud.models.User = Depends(get_current_user)
):
    wallet = crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet:
        wallet = crud.create_wallet(db, current_user.id)
    return {
        "coins_balance": wallet.coins_balance,
        "created_at": wallet.created_at
    }


# Statistiques du dashboard auteur
@router.get("/me/dashboard/author")
def get_author_dashboard(
    db: Session = Depends(get_db), 
    current_user: crud.models.User = Depends(get_current_user)
):
    if current_user.role != "author":
        raise HTTPException(status_code=403, detail="Seuls les auteurs peuvent accéder à ce dashboard")
    
    stats = crud.get_author_stats(db, current_user.id)
    return stats


# Statistiques du dashboard vendeur
@router.get("/me/dashboard/seller")
def get_seller_dashboard(
    db: Session = Depends(get_db), 
    current_user: crud.models.User = Depends(get_current_user)
):
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Seuls les vendeurs peuvent accéder à ce dashboard")
    
    stats = crud.get_seller_stats(db, current_user.id)
    return stats


# Obtenir un utilisateur par ID (DOIT ÊTRE À LA FIN)
@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user


# Supprimer un utilisateur (Admin)
@router.delete("/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: crud.models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    if crud.delete_user(db, user_id):
        return {"message": "Utilisateur supprimé"}
    raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

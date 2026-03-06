from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import DonationCreate, DonationOut
import crud, models

router = APIRouter(prefix="/api/donations", tags=["donations"])

# Dépendance DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper pour obtenir l'utilisateur actuel
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user


# Faire un don à un auteur
@router.post("/", response_model=DonationOut)
def create_donation(
    donation: DonationCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Vérifier que le montant est valide
    if donation.amount < 50:  # Minimum 50 coins (500 FCA)
        raise HTTPException(status_code=400, detail="Le montant minimum est de 50 coins")
    
    # Vérifier le solde
    wallet = crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet or wallet.coins_balance < donation.amount:
        raise HTTPException(status_code=400, detail="Solde insuffisant")
    
    # Vérifier le destinataire
    recipient = crud.get_user_by_id(db, donation.recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Destinataire non trouvé")
    
    # Vérifier le manga si spécifié
    if donation.manga_id:
        manga = crud.get_manga(db, donation.manga_id)
        if not manga:
            raise HTTPException(status_code=404, detail="Manga non trouvé")
        if manga.author_id != donation.recipient_id:
            raise HTTPException(status_code=400, detail="Le manga n'appartient pas à ce créateur")
    
    # Vérifier la boutique si spécifiée
    if donation.shop_id:
        shop = crud.get_shop(db, donation.shop_id)
        if not shop:
            raise HTTPException(status_code=404, detail="Boutique non trouvée")
        if shop.owner_id != donation.recipient_id:
            raise HTTPException(status_code=400, detail="La boutique n'appartient pas à ce vendeur")
    
    result = crud.create_donation(
        db,
        current_user.id,
        donation.recipient_id,
        donation.amount,
        donation.manga_id,
        donation.shop_id,
        donation.message
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Erreur lors du don")
    
    return result


# Obtenir les dons effectués par l'utilisateur
@router.get("/made", response_model=list[DonationOut])
def get_donations_made(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_donations_made(db, current_user.id, skip, limit)


# Obtenir les dons reçus par l'utilisateur
@router.get("/received", response_model=list[DonationOut])
def get_donations_received(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_donations_received(db, current_user.id, skip, limit)


# Obtenir les dons pour un auteur spécifique
@router.get("/author/{author_id}", response_model=list[DonationOut])
def get_author_donations(
    author_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    author = crud.get_user_by_id(db, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Auteur non trouvé")
    
    return crud.get_donations_received(db, author_id, skip, limit)


# Montants de don possibles
@router.get("/amounts")
def get_donation_amounts():
    return [
        {"amount": 50, "value_fcfa": 500, "badge": "Supporter Bronze"},
        {"amount": 100, "value_fcfa": 1000, "badge": "Supporter Argent"},
        {"amount": 200, "value_fcfa": 2000, "badge": "Supporter Or"},
        {"amount": 500, "value_fcfa": 5000, "badge": "Super Fan"}
    ]


# Badges de supporter
@router.get("/badges")
def get_supporter_badges():
    return {
        "bronze": {
            "name": "Supporter Bronze",
            "min_donations": 500,
            "description": "Pour les premiers supporters"
        },
        "silver": {
            "name": "Supporter Argent",
            "min_donations": 2000,
            "description": "Pour les supporters réguliers"
        },
        "gold": {
            "name": "Supporter Or",
            "min_donations": 5000,
            "description": "Pour les grands supporters"
        },
        "super_fan": {
            "name": "Super Fan",
            "min_donations": 10000,
            "description": "Pour les fans absolus"
        }
    }


# Statistiques des dons pour un auteur
@router.get("/author/{author_id}/stats")
def get_author_donation_stats(
    author_id: int, 
    db: Session = Depends(get_db)
):
    author = crud.get_user_by_id(db, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Auteur non trouvé")
    
    donations = crud.get_donations_received(db, author_id)
    
    total_received = sum(d.amount for d in donations)
    total_donors = len(set(d.donor_id for d in donations))
    
    return {
        "total_donations": len(donations),
        "total_coins_received": total_received,
        "total_value_fcfa": total_received * 10,
        "total_donors": total_donors,
        "average_donation": total_received // len(donations) if donations else 0
    }


# Faire un don personnalisé (montant libre)
@router.post("/custom", response_model=DonationOut)
def custom_donation(
    recipient_id: int,
    amount: int,
    message: str = None,
    manga_id: int = None,
    shop_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    donation_data = DonationCreate(
        recipient_id=recipient_id,
        amount=amount,
        message=message,
        manga_id=manga_id,
        shop_id=shop_id
    )
    return create_donation(donation_data, db, current_user)

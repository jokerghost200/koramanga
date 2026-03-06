from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import CoinPurchase, CoinTransactionOut, WithdrawalCreate, WithdrawalOut
import crud, models

router = APIRouter(prefix="/api/coins", tags=["coins"])

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


# Obtenir le solde du wallet
@router.get("/balance")
def get_balance(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    wallet = crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet:
        wallet = crud.create_wallet(db, current_user.id)
    return {
        "coins_balance": wallet.coins_balance,
        "balance_value_fcfa": wallet.coins_balance * 10  # 1 coin = 10FCFA
    }


# Acheter des coins (via Monetbil, Flutterwave, etc.)
@router.post("/purchase")
def purchase_coins(
    purchase: CoinPurchase, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Acheter des coins via paiement mobile
    - 1000 FCA = 100 KM Coins
    - Le paiement sera vérifié via le provider de paiement
    """
    # Calculer les coins basés sur le montant
    coins_received = purchase.amount // 10  # 10FCFA = 1 coin
    
    # Appliquer un bonus selon le pack
    if purchase.amount >= 10000:
        coins_received = int(coins_received * 1.3)  # Bonus 30%
    elif purchase.amount >= 5000:
        coins_received = int(coins_received * 1.2)  # Bonus 20%
    elif purchase.amount >= 1000:
        coins_received = int(coins_received * 1.1)  # Bonus 10%
    
    # Ajouter les coins (simulé - en production, vérifier le paiement)
    wallet = crud.add_coins(
        db, 
        current_user.id, 
        coins_received, 
        "deposit", 
        f"Purchase via {purchase.payment_method}",
        f"REF-{purchase.payment_method}-{purchase.phone_number}"
    )
    
    return {
        "message": "Achat de coins réussi",
        "amount_paid": purchase.amount,
        "coins_received": coins_received,
        "new_balance": wallet.coins_balance
    }


# Obtenir l'historique des transactions
@router.get("/transactions", response_model=list[CoinTransactionOut])
def get_transactions(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_coin_transactions(db, current_user.id, skip, limit)


# Retirer des gains (pour auteurs et vendeurs)
@router.post("/withdraw", response_model=WithdrawalOut)
def withdraw(
    withdrawal: WithdrawalCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["author", "seller"]:
        raise HTTPException(status_code=403, detail="Seuls les auteurs et vendeurs peuvent retirer des gains")
    
    # Vérifier le montant minimum (1000 coins = 10000 FCA)
    if withdrawal.amount < 1000:
        raise HTTPException(status_code=400, detail="Le montant minimum de retrait est de 1000 coins")
    
    wallet = crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet or wallet.coins_balance < withdrawal.amount:
        raise HTTPException(status_code=400, detail="Solde insuffisant")
    
    result = crud.create_withdrawal(
        db, 
        current_user.id, 
        withdrawal.amount, 
        withdrawal.method, 
        withdrawal.method_details
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Erreur lors du retrait")
    
    return result


# Obtenir l'historique des retraits
@router.get("/withdrawals", response_model=list[WithdrawalOut])
def get_my_withdrawals(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_withdrawals(db, current_user.id, skip, limit)


# Packs de coins disponibles
@router.get("/packs")
def get_coin_packs():
    return [
        {
            "id": "mini",
            "name": "Pack Mini",
            "price_fcfa": 500,
            "coins": 50,
            "bonus": 0,
            "description": "Pour commencer"
        },
        {
            "id": "standard",
            "name": "Pack Standard",
            "price_fcfa": 1000,
            "coins": 110,
            "bonus": 10,
            "description": "Le plus populaire"
        },
        {
            "id": "otaku",
            "name": "Pack Otaku",
            "price_fcfa": 5000,
            "coins": 600,
            "bonus": 100,
            "description": "Pour les fans"
        },
        {
            "id": "super_fan",
            "name": "Pack Super Fan",
            "price_fcfa": 10000,
            "coins": 1300,
            "bonus": 300,
            "description": "Pour les vrais fans"
        }
    ]


# Taux de conversion
@router.get("/rates")
def get_conversion_rates():
    return {
        "rate": "10 FCA = 1 KM Coin",
        "1_km_coin": "10 FCA",
        "withdrawal_minimum": "1000 coins (10000 FCA)",
        "commission": {
            "manga_sales": "20% (auteur: 80%)",
            "marketplace": "15% (vendeur: 85%)",
            "donations": "10% (créateur: 90%)"
        }
    }


# Admin: Lister tous les retraits
@router.get("/admin/withdrawals", response_model=list[WithdrawalOut])
def get_all_withdrawals(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    return crud.get_all_withdrawals(db, skip, limit)


# Admin: Approuver/rejeter un retrait
@router.put("/admin/withdrawals/{withdrawal_id}")
def process_withdrawal(
    withdrawal_id: int, 
    status: str, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    if status not in ["processing", "completed", "rejected"]:
        raise HTTPException(status_code=400, detail="Statut invalide")
    
    result = crud.update_withdrawal_status(db, withdrawal_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="Retrait non trouvé")
    
    return {"message": f"Retrait {status}", "withdrawal_id": withdrawal_id}

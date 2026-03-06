from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas import (
    ShopCreate, ShopUpdate, ShopOut, ShopDetailOut,
    ProductCreate, ProductUpdate, ProductOut,
    OrderCreate, OrderOut, OrderDetailOut, OrderItemOut
)
from app import crud, models

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

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


# ==================== SHOPS ====================

# Créer une boutique
@router.post("/shops", response_model=ShopOut)
def create_shop(
    shop: ShopCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "seller" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Seuls les vendeurs peuvent créer une boutique")
    
    return crud.create_shop(db, shop, current_user.id)


# Lister toutes les boutiques
@router.get("/shops", response_model=list[ShopOut])
def list_shops(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_shops(db, skip, limit)


# Obtenir une boutique par ID
@router.get("/shops/{shop_id}", response_model=ShopDetailOut)
def get_shop(shop_id: int, db: Session = Depends(get_db)):
    shop = crud.get_shop(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Boutique non trouvée")
    
    products_count = len(crud.get_products(db, shop_id=shop_id))
    
    return {
        **ShopOut.from_orm(shop).dict(),
        "products_count": products_count
    }


# Mettre à jour une boutique
@router.put("/shops/{shop_id}", response_model=ShopOut)
def update_shop(
    shop_id: int, 
    shop_update: ShopUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    shop = crud.get_shop(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Boutique non trouvée")
    
    if shop.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas modifier cette boutique")
    
    return crud.update_shop(db, shop_id, shop_update)


# Obtenir les boutiques de l'utilisateur
@router.get("/me/shops")
def get_my_shops(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_user_shops(db, current_user.id)


# ==================== PRODUCTS ====================

# Créer un produit
@router.post("/products", response_model=ProductOut)
def create_product(
    product: ProductCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "seller" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Seuls les vendeurs peuvent créer des produits")
    
    # Vérifier que la boutique appartient au vendeur
    shop = crud.get_shop(db, product.shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Boutique non trouvée")
    
    if shop.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cette boutique ne vous appartient pas")
    
    return crud.create_product(db, product, current_user.id)


# Lister tous les produits
@router.get("/products", response_model=list[ProductOut])
def list_products(
    skip: int = 0, 
    limit: int = 100, 
    category: str = None,
    shop_id: int = None,
    db: Session = Depends(get_db)
):
    if shop_id:
        return crud.get_products(db, skip, limit, shop_id)
    if category:
        return crud.get_products(db, skip, limit, category=category)
    return crud.get_all_products(db, skip, limit)


# Obtenir un produit par ID
@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    # Incrémenter les vues
    product.views += 1
    db.commit()
    
    return product


# Mettre à jour un produit
@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int, 
    product_update: ProductUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    if product.seller_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas modifier ce produit")
    
    return crud.update_product(db, product_id, product_update)


# Supprimer un produit
@router.delete("/products/{product_id}")
def delete_product(
    product_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    if product.seller_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer ce produit")
    
    if crud.delete_product(db, product_id):
        return {"message": "Produit supprimé"}
    raise HTTPException(status_code=400, detail="Erreur lors de la suppression")


# Catégories de produits
@router.get("/categories")
def get_categories():
    return [
        {"id": "figurines", "name": "Figurines", "icon": "🗿"},
        {"id": "vetements", "name": "Vêtements", "icon": "👕"},
        {"id": "posters", "name": "Posters", "icon": "🖼️"},
        {"id": "peluches", "name": "Peluches", "icon": "🧸"},
        {"id": "cosplays", "name": "Cosplays", "icon": "🎭"},
        {"id": "accessoires", "name": "Accessoires", "icon": "💎"},
        {"id": "artbooks", "name": "Artbooks", "icon": "📚"}
    ]


# ==================== ORDERS ====================

# Passer une commande
@router.post("/orders", response_model=OrderOut)
def create_order(
    order: OrderCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Vérifier le stock et calculer le total
    total = 0
    items_data = []
    
    for item in order.items:
        product = crud.get_product(db, item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Produit {item.product_id} non trouvé")
        if not product.is_active:
            raise HTTPException(status_code=400, detail=f"Produit {product.name} n'est plus disponible")
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Stock insuffisant pour {product.name}")
        
        total += product.price * item.quantity
        items_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": product.price
        })
    
    # Vérifier le solde en coins
    wallet = crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet or wallet.coins_balance < total:
        raise HTTPException(status_code=400, detail="Solde insuffisant")
    
    # Créer la commande
    result = crud.create_order(
        db, 
        current_user.id, 
        total, 
        items_data,
        order.shipping_address,
        order.shipping_phone
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Erreur lors de la création de la commande")
    
    # Déduire les coins
    crud.deduct_coins(db, current_user.id, total, "purchase", f"Order #{result.id}")
    
    return result


# Obtenir les commandes de l'utilisateur
@router.get("/orders", response_model=list[OrderOut])
def get_my_orders(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_user_orders(db, current_user.id, skip, limit)


# Obtenir une commande par ID
@router.get("/orders/{order_id}", response_model=OrderDetailOut)
def get_order(
    order_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Charger les items
    items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()
    
    return {
        **OrderOut.from_orm(order).dict(),
        "items": items
    }


# Obtenir les commandes du vendeur
@router.get("/seller/orders")
def get_seller_orders(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "seller" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Seuls les vendeurs peuvent voir leurs commandes")
    
    return crud.get_seller_orders(db, current_user.id)


# Mettre à jour le statut d'une commande
@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int, 
    status: str, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    # Vérifier les permissions
    product = db.query(models.Product).join(models.OrderItem).filter(
        models.OrderItem.order_id == order_id
    ).first()
    
    if product and product.seller_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    valid_statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Statut invalide")
    
    result = crud.update_order_status(db, order_id, status)
    if result:
        return {"message": "Statut mis à jour", "status": status}
    raise HTTPException(status_code=400, detail="Erreur lors de la mise à jour")

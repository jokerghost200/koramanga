from sqlalchemy.orm import Session
import models, utils
from datetime import date, datetime
from typing import Optional, List


# ==================== USER FUNCTIONS ====================

def create_user(db: Session, user):
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=utils.hash_password(user.password),
        role=user.role,
        phone=user.phone,
        sex=user.sex,
        city=user.city,
        country=user.country,
        birth_date=user.birth_date,
        profile_image=user.profile_image,
        bio=user.bio,
        created_at=datetime.now()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create wallet for user
    wallet = models.Wallet(
        user_id=db_user.id,
        coins_balance=0,
        created_at=datetime.now()
    )
    db.add(wallet)
    db.commit()
    
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, user_update):
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(user, key, value)
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


# ==================== WALLET & COINS FUNCTIONS ====================

def get_wallet_by_user_id(db: Session, user_id: int):
    return db.query(models.Wallet).filter(models.Wallet.user_id == user_id).first()


def create_wallet(db: Session, user_id: int):
    wallet = models.Wallet(
        user_id=user_id,
        coins_balance=0,
        created_at=datetime.now()
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


def add_coins(db: Session, user_id: int, amount: int, transaction_type: str, description: str = None, reference: str = None):
    wallet = get_wallet_by_user_id(db, user_id)
    if not wallet:
        wallet = create_wallet(db, user_id)
    
    wallet.coins_balance += amount
    wallet.updated_at = datetime.now()
    
    transaction = models.CoinTransaction(
        user_id=user_id,
        type=transaction_type,
        amount=amount,
        description=description,
        reference=reference,
        created_at=datetime.now()
    )
    db.add(transaction)
    db.commit()
    db.refresh(wallet)
    return wallet


def deduct_coins(db: Session, user_id: int, amount: int, transaction_type: str, description: str = None):
    wallet = get_wallet_by_user_id(db, user_id)
    if not wallet or wallet.coins_balance < amount:
        return None
    
    wallet.coins_balance -= amount
    wallet.updated_at = datetime.now()
    
    transaction = models.CoinTransaction(
        user_id=user_id,
        type=transaction_type,
        amount=-amount,
        description=description,
        created_at=datetime.now()
    )
    db.add(transaction)
    db.commit()
    db.refresh(wallet)
    return wallet


def get_coin_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.CoinTransaction).filter(
        models.CoinTransaction.user_id == user_id
    ).order_by(models.CoinTransaction.created_at.desc()).offset(skip).limit(limit).all()


# ==================== WITHDRAWAL FUNCTIONS ====================

def create_withdrawal(db: Session, user_id: int, amount: int, method: str, method_details: str = None):
    wallet = get_wallet_by_user_id(db, user_id)
    if not wallet or wallet.coins_balance < amount:
        return None
    
    # Deduct coins from wallet
    wallet.coins_balance -= amount
    wallet.updated_at = datetime.now()
    
    withdrawal = models.Withdrawal(
        user_id=user_id,
        amount=amount,
        method=method,
        method_details=method_details,
        status="pending",
        created_at=datetime.now()
    )
    db.add(withdrawal)
    
    transaction = models.CoinTransaction(
        user_id=user_id,
        type="withdraw",
        amount=-amount,
        description=f"Withdrawal via {method}",
        created_at=datetime.now()
    )
    db.add(transaction)
    db.commit()
    db.refresh(withdrawal)
    return withdrawal


def get_withdrawals(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Withdrawal).filter(
        models.Withdrawal.user_id == user_id
    ).order_by(models.Withdrawal.created_at.desc()).offset(skip).limit(limit).all()


def get_all_withdrawals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Withdrawal).order_by(
        models.Withdrawal.created_at.desc()
    ).offset(skip).limit(limit).all()


def update_withdrawal_status(db: Session, withdrawal_id: int, status: str):
    withdrawal = db.query(models.Withdrawal).filter(models.Withdrawal.id == withdrawal_id).first()
    if withdrawal:
        withdrawal.status = status
        if status == "completed":
            withdrawal.processed_at = datetime.now()
        db.commit()
        db.refresh(withdrawal)
        return withdrawal
    return None


# ==================== MANGA FUNCTIONS ====================

def create_manga(db: Session, manga, author_id: int):
    db_manga = models.Manga(
        title=manga.title,
        description=manga.description,
        cover_image=manga.cover_image,
        author_id=author_id,
        genre=manga.genre,
        is_premium=manga.is_premium,
        price_coins=manga.price_coins,
        status="draft",
        created_at=datetime.now()
    )
    db.add(db_manga)
    db.commit()
    db.refresh(db_manga)
    return db_manga


def get_manga(db: Session, manga_id: int):
    return db.query(models.Manga).filter(models.Manga.id == manga_id).first()


def get_mangas(db: Session, skip: int = 0, limit: int = 100, status: str = None, author_id: int = None):
    query = db.query(models.Manga)
    if status:
        query = query.filter(models.Manga.status == status)
    if author_id:
        query = query.filter(models.Manga.author_id == author_id)
    return query.order_by(models.Manga.created_at.desc()).offset(skip).limit(limit).all()


def get_published_mangas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Manga).filter(
        models.Manga.status == "published"
    ).order_by(models.Manga.created_at.desc()).offset(skip).limit(limit).all()


def update_manga(db: Session, manga_id: int, manga_update):
    manga = get_manga(db, manga_id)
    if not manga:
        return None
    for key, value in manga_update.dict(exclude_unset=True).items():
        setattr(manga, key, value)
    manga.updated_at = datetime.now()
    db.commit()
    db.refresh(manga)
    return manga


def delete_manga(db: Session, manga_id: int):
    manga = get_manga(db, manga_id)
    if manga:
        db.delete(manga)
        db.commit()
        return True
    return False


def publish_manga(db: Session, manga_id: int):
    manga = get_manga(db, manga_id)
    if manga:
        manga.status = "published"
        manga.updated_at = datetime.now()
        db.commit()
        db.refresh(manga)
        return manga
    return None


# ==================== CHAPTER FUNCTIONS ====================

def create_chapter(db: Session, chapter, manga_id: int):
    db_chapter = models.Chapter(
        manga_id=manga_id,
        title=chapter.title,
        chapter_number=chapter.chapter_number,
        price_coins=chapter.price_coins,
        is_premium=chapter.is_premium,
        thumbnail=chapter.thumbnail,
        created_at=datetime.now()
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter


def get_chapter(db: Session, chapter_id: int):
    return db.query(models.Chapter).filter(models.Chapter.id == chapter_id).first()


def get_chapters_by_manga(db: Session, manga_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Chapter).filter(
        models.Chapter.manga_id == manga_id
    ).order_by(models.Chapter.chapter_number.desc()).offset(skip).limit(limit).all()


def update_chapter(db: Session, chapter_id: int, chapter_update):
    chapter = get_chapter(db, chapter_id)
    if not chapter:
        return None
    for key, value in chapter_update.dict(exclude_unset=True).items():
        setattr(chapter, key, value)
    chapter.updated_at = datetime.now()
    db.commit()
    db.refresh(chapter)
    return chapter


def delete_chapter(db: Session, chapter_id: int):
    chapter = get_chapter(db, chapter_id)
    if chapter:
        db.delete(chapter)
        db.commit()
        return True
    return False


# ==================== CHAPTER PAGE FUNCTIONS ====================

def create_chapter_page(db: Session, page):
    db_page = models.ChapterPage(
        chapter_id=page.chapter_id,
        page_number=page.page_number,
        image_url=page.image_url,
        original_filename=page.original_filename,
        file_size=page.file_size,
        width=page.width,
        height=page.height,
        created_at=datetime.now()
    )
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page


def get_chapter_pages(db: Session, chapter_id: int):
    return db.query(models.ChapterPage).filter(
        models.ChapterPage.chapter_id == chapter_id
    ).order_by(models.ChapterPage.page_number).all()


# ==================== PURCHASE & LIBRARY FUNCTIONS ====================

def purchase_manga(db: Session, user_id: int, manga_id: int, amount: int):
    # Deduct coins
    wallet = deduct_coins(db, user_id, amount, "purchase", f"Purchase manga {manga_id}")
    if not wallet:
        return None
    
    # Create purchase record
    purchase = models.MangaPurchase(
        user_id=user_id,
        manga_id=manga_id,
        amount_paid=amount,
        created_at=datetime.now()
    )
    db.add(purchase)
    
    # Add to library
    library_item = models.LibraryItem(
        user_id=user_id,
        manga_id=manga_id,
        created_at=datetime.now()
    )
    db.add(library_item)
    
    db.commit()
    db.refresh(purchase)
    return purchase


def get_manga_purchase(db: Session, user_id: int, manga_id: int):
    return db.query(models.MangaPurchase).filter(
        models.MangaPurchase.user_id == user_id,
        models.MangaPurchase.manga_id == manga_id
    ).first()


def get_user_purchases(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.MangaPurchase).filter(
        models.MangaPurchase.user_id == user_id
    ).order_by(models.MangaPurchase.created_at.desc()).offset(skip).limit(limit).all()


def add_to_library(db: Session, user_id: int, manga_id: int):
    existing = db.query(models.LibraryItem).filter(
        models.LibraryItem.user_id == user_id,
        models.LibraryItem.manga_id == manga_id
    ).first()
    
    if existing:
        return existing
    
    library_item = models.LibraryItem(
        user_id=user_id,
        manga_id=manga_id,
        created_at=datetime.now()
    )
    db.add(library_item)
    db.commit()
    db.refresh(library_item)
    return library_item


def get_library(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.LibraryItem).filter(
        models.LibraryItem.user_id == user_id
    ).order_by(models.LibraryItem.updated_at.desc()).offset(skip).limit(limit).all()


def update_library_item(db: Session, library_item_id: int, update_data):
    item = db.query(models.LibraryItem).filter(models.LibraryItem.id == library_item_id).first()
    if not item:
        return None
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(item, key, value)
    item.updated_at = datetime.now()
    db.commit()
    db.refresh(item)
    return item


def is_manga_in_library(db: Session, user_id: int, manga_id: int):
    item = db.query(models.LibraryItem).filter(
        models.LibraryItem.user_id == user_id,
        models.LibraryItem.manga_id == manga_id
    ).first()
    return item is not None


# ==================== DONATION FUNCTIONS ====================

def create_donation(db: Session, donor_id: int, recipient_id: int, amount: int, manga_id: int = None, shop_id: int = None, message: str = None):
    # Deduct coins from donor
    wallet = deduct_coins(db, donor_id, amount, "donation", f"Donation to user {recipient_id}")
    if not wallet:
        return None
    
    # Calculate commission (10%)
    commission = int(amount * 0.1)
    recipient_amount = amount - commission
    
    # Create donation record
    donation = models.Donation(
        donor_id=donor_id,
        recipient_id=recipient_id,
        manga_id=manga_id,
        shop_id=shop_id,
        amount=amount,
        message=message,
        created_at=datetime.now()
    )
    db.add(donation)
    
    # Add coins to recipient (90%)
    recipient_wallet = get_wallet_by_user_id(db, recipient_id)
    if recipient_wallet:
        recipient_wallet.coins_balance += recipient_amount
        recipient_wallet.updated_at = datetime.now()
        
        transaction = models.CoinTransaction(
            user_id=recipient_id,
            type="donation",
            amount=recipient_amount,
            description=f"Donation received from user {donor_id}",
            created_at=datetime.now()
        )
        db.add(transaction)
    
    db.commit()
    db.refresh(donation)
    return donation


def get_donations_made(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Donation).filter(
        models.Donation.donor_id == user_id
    ).order_by(models.Donation.created_at.desc()).offset(skip).limit(limit).all()


def get_donations_received(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Donation).filter(
        models.Donation.recipient_id == user_id
    ).order_by(models.Donation.created_at.desc()).offset(skip).limit(limit).all()


# ==================== SHOP FUNCTIONS ====================

def create_shop(db: Session, shop, owner_id: int):
    db_shop = models.Shop(
        owner_id=owner_id,
        name=shop.name,
        description=shop.description,
        logo=shop.logo,
        banner=shop.banner,
        created_at=datetime.now()
    )
    db.add(db_shop)
    db.commit()
    db.refresh(db_shop)
    return db_shop


def get_shop(db: Session, shop_id: int):
    return db.query(models.Shop).filter(models.Shop.id == shop_id).first()


def get_shops(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Shop).filter(
        models.Shop.is_active == True
    ).order_by(models.Shop.created_at.desc()).offset(skip).limit(limit).all()


def get_user_shops(db: Session, user_id: int):
    return db.query(models.Shop).filter(models.Shop.owner_id == user_id).all()


def update_shop(db: Session, shop_id: int, shop_update):
    shop = get_shop(db, shop_id)
    if not shop:
        return None
    for key, value in shop_update.dict(exclude_unset=True).items():
        setattr(shop, key, value)
    shop.updated_at = datetime.now()
    db.commit()
    db.refresh(shop)
    return shop


# ==================== PRODUCT FUNCTIONS ====================

def create_product(db: Session, product, seller_id: int):
    db_product = models.Product(
        shop_id=product.shop_id,
        seller_id=seller_id,
        name=product.name,
        description=product.description,
        category=product.category,
        price=product.price,
        stock=product.stock,
        images=product.images,
        is_active=product.is_active,
        created_at=datetime.now()
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100, shop_id: int = None, category: str = None):
    query = db.query(models.Product).filter(models.Product.is_active == True)
    if shop_id:
        query = query.filter(models.Product.shop_id == shop_id)
    if category:
        query = query.filter(models.Product.category == category)
    return query.order_by(models.Product.created_at.desc()).offset(skip).limit(limit).all()


def get_all_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).order_by(
        models.Product.created_at.desc()
    ).offset(skip).limit(limit).all()


def update_product(db: Session, product_id: int, product_update):
    product = get_product(db, product_id)
    if not product:
        return None
    for key, value in product_update.dict(exclude_unset=True).items():
        setattr(product, key, value)
    product.updated_at = datetime.now()
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int):
    product = get_product(db, product_id)
    if product:
        db.delete(product)
        db.commit()
        return True
    return False


# ==================== ORDER FUNCTIONS ====================

def create_order(db: Session, user_id: int, total: int, items: List, shipping_address: str = None, shipping_phone: str = None):
    order = models.Order(
        user_id=user_id,
        total=total,
        shipping_address=shipping_address,
        shipping_phone=shipping_phone,
        status="pending",
        created_at=datetime.now()
    )
    db.add(order)
    db.flush()
    
    for item in items:
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price,
            created_at=datetime.now()
        )
        db.add(order_item)
        
        # Update product stock
        product = get_product(db, item.product_id)
        if product:
            product.stock -= item.quantity
    
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Order).filter(
        models.Order.user_id == user_id
    ).order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()


def get_seller_orders(db: Session, seller_id: int):
    return db.query(models.Order).join(models.OrderItem).filter(
        models.OrderItem.product_id.in_(
            db.query(models.Product.id).filter(models.Product.seller_id == seller_id)
        )
    ).distinct().all()


def update_order_status(db: Session, order_id: int, status: str):
    order = get_order(db, order_id)
    if order:
        order.status = status
        order.updated_at = datetime.now()
        db.commit()
        db.refresh(order)
        return order
    return None


# ==================== COMMENT FUNCTIONS ====================

def create_comment(db: Session, user_id: int, manga_id: int, content: str):
    comment = models.Comment(
        user_id=user_id,
        manga_id=manga_id,
        content=content,
        is_approved=True,
        created_at=datetime.now()
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments_by_manga(db: Session, manga_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Comment).filter(
        models.Comment.manga_id == manga_id,
        models.Comment.is_approved == True
    ).order_by(models.Comment.created_at.desc()).offset(skip).limit(limit).all()


def delete_comment(db: Session, comment_id: int):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if comment:
        db.delete(comment)
        db.commit()
        return True
    return False


# ==================== STATS FUNCTIONS ====================

def get_author_stats(db: Session, author_id: int):
    mangas = db.query(models.Manga).filter(models.Manga.author_id == author_id).all()
    manga_ids = [m.id for m in mangas]
    
    purchases = db.query(models.MangaPurchase).filter(
        models.MangaPurchase.manga_id.in_(manga_ids)
    ).all() if manga_ids else []
    
    donations = db.query(models.Donation).filter(
        models.Donation.recipient_id == author_id
    ).all()
    
    chapters_count = db.query(models.Chapter).filter(
        models.Chapter.manga_id.in_(manga_ids)
    ).count() if manga_ids else 0
    
    return {
        "total_mangas": len(mangas),
        "total_chapters": chapters_count,
        "total_sales": len(purchases),
        "total_revenue": sum(p.amount_paid for p in purchases),
        "total_donations_received": sum(d.amount for d in donations)
    }


def get_seller_stats(db: Session, seller_id: int):
    products = db.query(models.Product).filter(models.Product.seller_id == seller_id).all()
    product_ids = [p.id for p in products]
    
    orders = db.query(models.Order).join(models.OrderItem).filter(
        models.OrderItem.product_id.in_(product_ids)
    ).distinct().all() if product_ids else []
    
    return {
        "total_products": len(products),
        "total_orders": len(orders),
        "total_sales": sum(o.total for o in orders)
    }

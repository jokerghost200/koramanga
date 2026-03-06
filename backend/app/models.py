from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

# Rôles utilisateur
class UserRole(enum.Enum):
    VISITOR = "visitor"
    LECTOR = "lector"
    AUTHOR = "author"
    SELLER = "seller"
    ADMIN = "admin"

# Statut du manga
class MangaStatus(enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"
    REJECTED = "rejected"

# Statut de la commande
class OrderStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Statut du retrait
class WithdrawalStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"

# Type de transaction coin
class CoinTransactionType(enum.Enum):
    DEPOSIT = "deposit"
    PURCHASE = "purchase"
    DONATION = "donation"
    WITHDRAW = "withdraw"
    COMMISSION = "commission"

# Badge de supporter
class SupporterBadge(enum.Enum):
    NONE = "none"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    SUPER_FAN = "super_fan"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="visitor")
    phone = Column(String, nullable=True)
    sex = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    profile_image = Column(String, nullable=True)
    id_card_image = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    supporter_badge = Column(String, default="none")
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=True)

    # Relations
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    manga_purchases = relationship("MangaPurchase", back_populates="user")
    library = relationship("LibraryItem", back_populates="user")
    donations_made = relationship("Donation", foreign_keys="Donation.donor_id", back_populates="donor")
    donations_received = relationship("Donation", foreign_keys="Donation.recipient_id", back_populates="recipient")
    orders = relationship("Order", back_populates="user")
    products = relationship("Product", back_populates="seller")
    withdrawals = relationship("Withdrawal", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    shops = relationship("Shop", back_populates="owner")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    coins_balance = Column(Integer, default=0)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=True)

    user = relationship("User", back_populates="wallet")


class CoinTransaction(Base):
    __tablename__ = "coin_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    created_at = Column(Date, nullable=False)

    user = relationship("User", back_populates="wallet")


class Manga(Base):
    __tablename__ = "mangas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    cover_image = Column(String, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    genre = Column(String, nullable=True)
    status = Column(String, default="draft")
    is_premium = Column(Boolean, default=False)
    price_coins = Column(Integer, default=0)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=True)

    author = relationship("User", back_populates="mangas")
    chapters = relationship("Chapter", back_populates="manga")
    purchases = relationship("MangaPurchase", back_populates="manga")
    library_items = relationship("LibraryItem", back_populates="manga")
    comments = relationship("Comment", back_populates="manga")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    manga_id = Column(Integer, ForeignKey("mangas.id"), nullable=False)
    title = Column(String, nullable=False)
    chapter_number = Column(Integer, nullable=False)
    price_coins = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    thumbnail = Column(String, nullable=True)
    views = Column(Integer, default=0)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=True)

    manga = relationship("Manga", back_populates="chapters")
    pages = relationship("ChapterPage", back_populates="chapter")


class ChapterPage(Base):
    __tablename__ = "chapter_pages"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_url = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(Date, nullable=False)

    chapter = relationship("Chapter", back_populates="pages")


class MangaPurchase(Base):
    __tablename__ = "manga_purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    manga_id = Column(Integer, ForeignKey("mangas.id"), nullable=False)
    amount_paid = Column(Integer, nullable=False)
    created_at = Column(Date, nullable=False)

    user = relationship("User", back_populates="manga_purchases")
    manga = relationship("Manga", back_populates="purchases")


class LibraryItem(Base):
    __tablename__ = "library_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    manga_id = Column(Integer, ForeignKey("mangas.id"), nullable=False)
    last_chapter_read = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
    is_downloaded = Column(Boolean, default=False)
    download_quality = Column(String, nullable=True)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=True)

    user = relationship("User", back_populates="library")
    manga = relationship("Manga", back_populates="library_items")


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    donor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    manga_id = Column(Integer, ForeignKey("mangas.id"), nullable=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True)
    amount = Column(Integer, nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(Date, nullable=False)

    donor = relationship("User", foreign_keys=[donor_id], back_populates="donations_made")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="donations_received")


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    logo = Column(String, nullable=True)
    banner = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    total_sales = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=True)

    owner = relationship("User", back_populates="shops")
    products = relationship("Product", back_populates="shop")
    donations = relationship("Donation", back_populates="shop")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, default=0)
    images = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=True)

    shop = relationship("Shop", back_populates="products")
    seller = relationship("User", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total = Column(Integer, nullable=False)
    status = Column(String, default="pending")
    shipping_address = Column(Text, nullable=True)
    shipping_phone = Column(String, nullable=True)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=True)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Integer, nullable=False)
    created_at = Column(Date, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    manga_id = Column(Integer, ForeignKey("mangas.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=True)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=True)

    user = relationship("User", back_populates="comments")
    manga = relationship("Manga", back_populates="comments")


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    method = Column(String, nullable=False)
    method_details = Column(String, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(Date, nullable=False)
    processed_at = Column(Date, nullable=True)

    user = relationship("User", back_populates="withdrawals")

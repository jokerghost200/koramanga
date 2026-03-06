from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List

# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "visitor"
    phone: Optional[str] = None
    sex: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    birth_date: Optional[date] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    phone: Optional[str] = None
    sex: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    birth_date: Optional[date] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None


class UserOut(UserBase):
    id: int
    is_active: bool = True
    is_verified: bool = False
    supporter_badge: str = "none"
    created_at: datetime

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


# ==================== WALLET & COINS SCHEMAS ====================

class WalletBase(BaseModel):
    pass


class WalletOut(WalletBase):
    id: int
    user_id: int
    coins_balance: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class CoinTransactionBase(BaseModel):
    type: str
    amount: int
    description: Optional[str] = None
    reference: Optional[str] = None


class CoinTransactionCreate(CoinTransactionBase):
    pass


class CoinTransactionOut(CoinTransactionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class CoinPurchase(BaseModel):
    amount: int
    payment_method: str
    phone_number: str


class WithdrawalBase(BaseModel):
    amount: int
    method: str
    method_details: Optional[str] = None


class WithdrawalCreate(WithdrawalBase):
    pass


class WithdrawalOut(WithdrawalBase):
    id: int
    user_id: int
    status: str = "pending"
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ==================== MANGA SCHEMAS ====================

class MangaBase(BaseModel):
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    genre: Optional[str] = None
    is_premium: bool = False
    price_coins: int = 0


class MangaCreate(MangaBase):
    pass


class MangaUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    genre: Optional[str] = None
    is_premium: Optional[bool] = None
    price_coins: Optional[int] = None
    status: Optional[str] = None


class MangaOut(MangaBase):
    id: int
    author_id: int
    status: str = "draft"
    views: int = 0
    likes: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class MangaDetailOut(MangaOut):
    chapters_count: int = 0


# ==================== CHAPTER SCHEMAS ====================

class ChapterBase(BaseModel):
    title: str
    chapter_number: int
    price_coins: int = 0
    is_premium: bool = False
    thumbnail: Optional[str] = None


class ChapterCreate(ChapterBase):
    manga_id: int


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    chapter_number: Optional[int] = None
    price_coins: Optional[int] = None
    is_premium: Optional[bool] = None
    thumbnail: Optional[str] = None


class ChapterOut(ChapterBase):
    id: int
    manga_id: int
    views: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ChapterDetailOut(ChapterOut):
    pages_count: int = 0


# ==================== CHAPTER PAGE SCHEMAS ====================

class ChapterPageBase(BaseModel):
    page_number: int
    image_url: str
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ChapterPageCreate(ChapterPageBase):
    chapter_id: int


class ChapterPageOut(ChapterPageBase):
    id: int
    chapter_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ==================== PURCHASE & LIBRARY SCHEMAS ====================

class MangaPurchaseBase(BaseModel):
    manga_id: int
    amount_paid: int


class MangaPurchaseCreate(MangaPurchaseBase):
    pass


class MangaPurchaseOut(MangaPurchaseBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class LibraryItemBase(BaseModel):
    manga_id: int
    last_chapter_read: int = 0
    progress: float = 0.0
    is_downloaded: bool = False
    download_quality: Optional[str] = None


class LibraryItemCreate(LibraryItemBase):
    pass


class LibraryItemUpdate(BaseModel):
    last_chapter_read: Optional[int] = None
    progress: Optional[float] = None
    is_downloaded: Optional[bool] = None
    download_quality: Optional[str] = None


class LibraryItemOut(LibraryItemBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ==================== DONATION SCHEMAS ====================

class DonationBase(BaseModel):
    recipient_id: int
    manga_id: Optional[int] = None
    shop_id: Optional[int] = None
    amount: int
    message: Optional[str] = None


class DonationCreate(DonationBase):
    pass


class DonationOut(DonationBase):
    id: int
    donor_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ==================== SHOP SCHEMAS ====================

class ShopBase(BaseModel):
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    banner: Optional[str] = None


class ShopCreate(ShopBase):
    pass


class ShopUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    banner: Optional[str] = None
    is_active: Optional[bool] = None


class ShopOut(ShopBase):
    id: int
    owner_id: int
    is_active: bool = True
    total_sales: int = 0
    rating: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ShopDetailOut(ShopOut):
    products_count: int = 0


# ==================== PRODUCT SCHEMAS ====================

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: int
    stock: int = 0
    images: Optional[str] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    shop_id: int


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[int] = None
    stock: Optional[int] = None
    images: Optional[str] = None
    is_active: Optional[bool] = None


class ProductOut(ProductBase):
    id: int
    shop_id: int
    seller_id: int
    views: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ==================== ORDER SCHEMAS ====================

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = 1
    price: int


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemOut(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class OrderBase(BaseModel):
    total: int
    shipping_address: Optional[str] = None
    shipping_phone: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_phone: Optional[str] = None


class OrderOut(OrderBase):
    id: int
    user_id: int
    status: str = "pending"
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class OrderDetailOut(OrderOut):
    items: List[OrderItemOut] = []


# ==================== COMMENT SCHEMAS ====================

class CommentBase(BaseModel):
    manga_id: int
    content: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: Optional[str] = None
    is_approved: Optional[bool] = None


class CommentOut(CommentBase):
    id: int
    user_id: int
    is_approved: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ==================== STATS SCHEMAS ====================

class DashboardStats(BaseModel):
    total_mangas: int = 0
    total_chapters: int = 0
    total_sales: int = 0
    total_revenue: int = 0
    total_donations_received: int = 0
    total_products: int = 0
    total_orders: int = 0


class MangaStats(BaseModel):
    views: int = 0
    likes: int = 0
    purchases: int = 0
    revenue: int = 0
    donations: int = 0

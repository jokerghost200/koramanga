from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import ChapterCreate, ChapterUpdate, ChapterOut, ChapterDetailOut, ChapterPageCreate, ChapterPageOut
import crud, models
from datetime import datetime

router = APIRouter(prefix="/api/chapters", tags=["chapters"])

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


# Créer un chapitre (Auteur uniquement)
@router.post("/", response_model=ChapterOut)
def create_chapter(
    chapter: ChapterCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["author", "admin"]:
        raise HTTPException(status_code=403, detail="Seuls les auteurs peuvent créer des chapitres")
    
    manga = crud.get_manga(db, chapter.manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga non trouvé")
    
    if manga.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas ajouter de chapitre à ce manga")
    
    # Vérifier si le numéro de chapitre existe déjà
    existing = db.query(models.Chapter).filter(
        models.Chapter.manga_id == chapter.manga_id,
        models.Chapter.chapter_number == chapter.chapter_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro de chapitre existe déjà")
    
    return crud.create_chapter(db, chapter, chapter.manga_id)


# Obtenir un chapitre par ID
@router.get("/{chapter_id}", response_model=ChapterDetailOut)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    chapter = crud.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre non trouvé")
    
    # Incrémenter les vues
    chapter.views += 1
    db.commit()
    
    # Compter les pages
    pages = crud.get_chapter_pages(db, chapter_id)
    
    return {
        **ChapterOut.from_orm(chapter).dict(),
        "pages_count": len(pages)
    }


# Mettre à jour un chapitre
@router.put("/{chapter_id}", response_model=ChapterOut)
def update_chapter(
    chapter_id: int, 
    chapter_update: ChapterUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    chapter = crud.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre non trouvé")
    
    manga = crud.get_manga(db, chapter.manga_id)
    if manga.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas modifier ce chapitre")
    
    return crud.update_chapter(db, chapter_id, chapter_update)


# Supprimer un chapitre
@router.delete("/{chapter_id}")
def delete_chapter(
    chapter_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    chapter = crud.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre non trouvé")
    
    manga = crud.get_manga(db, chapter.manga_id)
    if manga.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer ce chapitre")
    
    if crud.delete_chapter(db, chapter_id):
        return {"message": "Chapitre supprimé"}
    raise HTTPException(status_code=400, detail="Erreur lors de la suppression")


# Obtenir les pages d'un chapitre
@router.get("/{chapter_id}/pages")
def get_chapter_pages(chapter_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    chapter = crud.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre non trouvé")
    
    manga = crud.get_manga(db, chapter.manga_id)
    
    # Vérifier si l'utilisateur peut lire ce chapitre
    in_library = crud.is_manga_in_library(db, current_user.id, chapter.manga_id)
    
    if chapter.is_premium and not in_library and manga.price_coins > 0:
        raise HTTPException(status_code=403, detail="Vous devez d'abord acheter ce manga pour lire ce chapitre")
    
    if manga.is_premium and not in_library and manga.price_coins > 0:
        raise HTTPException(status_code=403, detail="Vous devez d'abord acheter ce manga pour lire ce chapitre")
    
    return crud.get_chapter_pages(db, chapter_id)


# Ajouter une page à un chapitre
@router.post("/{chapter_id}/pages", response_model=ChapterPageOut)
def add_chapter_page(
    chapter_id: int, 
    page: ChapterPageCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    chapter = crud.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre non trouvé")
    
    manga = crud.get_manga(db, chapter.manga_id)
    if manga.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas ajouter de page à ce chapitre")
    
    return crud.create_chapter_page(db, page)


# Acheter un chapitre
@router.post("/{chapter_id}/purchase")
def purchase_chapter(
    chapter_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    chapter = crud.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre non trouvé")
    
    manga = crud.get_manga(db, chapter.manga_id)
    
    # Vérifier si déjà acheté
    in_library = crud.is_manga_in_library(db, current_user.id, manga.id)
    if in_library:
        raise HTTPException(status_code=400, detail="Vous avez déjà ce manga dans votre bibliothèque")
    
    if not chapter.is_premium and not manga.is_premium:
        raise HTTPException(status_code=400, detail="Ce chapitre est gratuit")
    
    wallet = crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet or wallet.coins_balance < chapter.price_coins:
        raise HTTPException(status_code=400, detail="Solde insuffisant")
    
    # Acheter le manga entier
    purchase = crud.purchase_manga(db, current_user.id, manga.id, manga.price_coins)
    if not purchase:
        raise HTTPException(status_code=400, detail="Erreur lors de l'achat")
    
    return {"message": "Achat réussi", "manga_id": manga.id}


# Lire un chapitre (mettre à jour la progression)
@router.post("/{chapter_id}/read")
def read_chapter(
    chapter_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    chapter = crud.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre non trouvé")
    
    manga = crud.get_manga(db, chapter.manga_id)
    
    # Vérifier l'accès
    in_library = crud.is_manga_in_library(db, current_user.id, manga.id)
    if not in_library and (manga.is_premium or chapter.is_premium):
        raise HTTPException(status_code=403, detail="Vous devez d'abord acheter ce manga")
    
    # Mettre à jour la progression dans la bibliothèque
    library_item = db.query(models.LibraryItem).filter(
        models.LibraryItem.user_id == current_user.id,
        models.LibraryItem.manga_id == manga.id
    ).first()
    
    if library_item:
        if chapter.chapter_number > library_item.last_chapter_read:
            library_item.last_chapter_read = chapter.chapter_number
            # Calculer la progression (simplifiée)
            chapters = crud.get_chapters_by_manga(db, manga.id)
            if chapters:
                library_item.progress = (chapter.chapter_number / len(chapters)) * 100
            library_item.updated_at = datetime.now()
            db.commit()
    
    return {"message": "Progression mise à jour", "chapter_number": chapter.chapter_number}


# Marquer comme téléchargé pour lecture hors ligne
@router.post("/{chapter_id}/download")
def download_chapter(
    chapter_id: int, 
    quality: str = "standard",
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    chapter = crud.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre non trouvé")
    
    manga = crud.get_manga(db, chapter.manga_id)
    
    # Vérifier l'accès
    in_library = crud.is_manga_in_library(db, current_user.id, manga.id)
    if not in_library:
        raise HTTPException(status_code=403, detail="Vous devez d'abord acheter ce manga")
    
    # Mettre à jour le statut de téléchargement
    library_item = db.query(models.LibraryItem).filter(
        models.LibraryItem.user_id == current_user.id,
        models.LibraryItem.manga_id == manga.id
    ).first()
    
    if library_item:
        library_item.is_downloaded = True
        library_item.download_quality = quality
        library_item.updated_at = datetime.now()
        db.commit()
    
    return {"message": "Téléchargement activé", "quality": quality}

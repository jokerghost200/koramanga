from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas import MangaCreate, MangaUpdate, MangaOut, MangaDetailOut, CommentCreate, CommentOut
from app import crud, models

router = APIRouter(prefix="/api/mangas", tags=["mangas"])

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


# Lister tous les mangas publiés
@router.get("/", response_model=list[MangaOut])
def list_mangas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_published_mangas(db, skip, limit)


# Rechercher des mangas
@router.get("/search")
def search_mangas(q: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    mangas = db.query(models.Manga).filter(
        models.Manga.status == "published",
        models.Manga.title.contains(q)
    ).offset(skip).limit(limit).all()
    return mangas


# Obtenir les mangas de l'auteur connecté
@router.get("/me/mangas")
def get_my_mangas(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["author", "admin"]:
        raise HTTPException(status_code=403, detail="Seuls les auteurs peuvent voir leurs mangas")
    return crud.get_mangas(db, author_id=current_user.id)


# Créer un manga (Auteur uniquement)
@router.post("/", response_model=MangaOut)
def create_manga(
    manga: MangaCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["author", "admin"]:
        raise HTTPException(status_code=403, detail="Seuls les auteurs peuvent créer des mangas")
    
    return crud.create_manga(db, manga, current_user.id)


# Obtenir un manga par ID (doit être à la fin)
@router.get("/{manga_id}", response_model=MangaDetailOut)
def get_manga(manga_id: int, db: Session = Depends(get_db)):
    manga = crud.get_manga(db, manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga non trouvé")
    
    # Incrémenter les vues
    manga.views += 1
    db.commit()
    
    # Compter les chapitres
    chapters_count = len(crud.get_chapters_by_manga(db, manga_id))
    
    return {
        **MangaOut.from_orm(manga).dict(),
        "chapters_count": chapters_count
    }


# Mettre à jour un manga
@router.put("/{manga_id}", response_model=MangaOut)
def update_manga(
    manga_id: int, 
    manga_update: MangaUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    manga = crud.get_manga(db, manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga non trouvé")
    
    if manga.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas modifier ce manga")
    
    return crud.update_manga(db, manga_id, manga_update)


# Publier un manga
@router.post("/{manga_id}/publish")
def publish_manga(
    manga_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    manga = crud.get_manga(db, manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga non trouvé")
    
    if manga.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas publier ce manga")
    
    result = crud.publish_manga(db, manga_id)
    if result:
        return {"message": "Manga publié avec succès"}
    raise HTTPException(status_code=400, detail="Erreur lors de la publication")


# Supprimer un manga
@router.delete("/{manga_id}")
def delete_manga(
    manga_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    manga = crud.get_manga(db, manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga non trouvé")
    
    if manga.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer ce manga")
    
    if crud.delete_manga(db, manga_id):
        return {"message": "Manga supprimé"}
    raise HTTPException(status_code=400, detail="Erreur lors de la suppression")


# Lister les chapitres d'un manga
@router.get("/{manga_id}/chapters")
def get_manga_chapters(manga_id: int, db: Session = Depends(get_db)):
    manga = crud.get_manga(db, manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga non trouvé")
    return crud.get_chapters_by_manga(db, manga_id)


# Ajouter un manga à la bibliothèque
@router.post("/{manga_id}/library")
def add_to_library(
    manga_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    manga = crud.get_manga(db, manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga non trouvé")
    
    # Vérifier si l'utilisateur a acheté le manga
    purchase = crud.get_manga_purchase(db, current_user.id, manga_id)
    if not purchase and manga.price_coins > 0:
        raise HTTPException(status_code=403, detail="Vous devez d'abord acheter ce manga")
    
    item = crud.add_to_library(db, current_user.id, manga_id)
    if not item:
        raise HTTPException(status_code=400, detail="Erreur lors de l'ajout à la bibliothèque")
    
    return {"message": "Manga ajouté à la bibliothèque"}


# Like un manga
@router.post("/{manga_id}/like")
def like_manga(
    manga_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    manga = crud.get_manga(db, manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga non trouvé")
    
    manga.likes += 1
    db.commit()
    
    return {"message": "Manga liké", "likes": manga.likes}


# Commenter un manga
@router.post("/{manga_id}/comments", response_model=CommentOut)
def add_comment(
    manga_id: int, 
    comment: CommentCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    manga = crud.get_manga(db, manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga non trouvé")
    
    return crud.create_comment(db, current_user.id, manga_id, comment.content)


# Lister les commentaires d'un manga
@router.get("/{manga_id}/comments")
def get_manga_comments(manga_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_comments_by_manga(db, manga_id, skip, limit)

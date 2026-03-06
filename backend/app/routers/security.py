from fastapi import APIRouter, Depends, HTTPException, Header, Response
from database import SessionLocal
from utils import security as security_utils

router = APIRouter(prefix="/api/security", tags=["security"])

# Dépendance DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Obtenir les en-têtes de sécurité
@router.get("/headers")
def get_security_headers():
    """
    Retourne les en-têtes de sécurité à utiliser côté frontend.
    """
    return security_utils.get_security_headers()


# Générer un token temporaire pour une image
@router.post("/image/token")
def get_secure_image_token(
    image_path: str,
    content_id: int,
    user_id: int = 1  # Par défaut, à remplacer par l'utilisateur connecté
):
    """
    Génère un token temporaire pour accéder à une image protégée.
    Le token expire après 1 heure.
    """
    result = security_utils.get_secure_image_url(image_path, user_id, content_id)
    return result


# Vérifier un token
@router.post("/token/verify")
def verify_token(token: str):
    """
    Vérifie si un token est valide.
    """
    result = security_utils.verify_token(token)
    if not result:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return {"valid": True, "data": result}


# Révoquer un token
@router.post("/token/revoke")
def revoke_token(token: str):
    """
    Révoque un token (pour la déconnexion).
    """
    result = security_utils.revoke_token(token)
    if result:
        return {"message": "Token révoqué"}
    return {"message": "Token non trouvé"}


# Générer un watermark pour l'utilisateur
@router.get("/watermark")
def get_watermark(user_id: int, username: str):
    """
    Génère le texte de watermark dynamique pour protéger les images.
    """
    return {
        "watermark_text": security_utils.generate_watermark_text(user_id, username)
    }


# Configuration de sécurité pour le lecteur de manga
@router.get("/reader/config")
def get_reader_security_config():
    """
    Retourne la configuration de sécurité pour le lecteur de manga.
    Ces paramètres doivent être utilisés côté frontend (PWA).
    """
    return {
        "protection": {
            "disable_right_click": True,
            "disable_copy_paste": True,
            "disable_screenshots": True,  # Note: Fonctionne sur mobile avec FLAG_SECURE
            "show_watermark": True,
            "watermark_opacity": 0.3,
            "watermark_position": "diagonal"
        },
        "offline": {
            "enabled": True,
            "cache_images": True,
            "max_cache_size_mb": 500,
            "encrypted_storage": True
        },
        "headers": security_utils.get_security_headers()
    }

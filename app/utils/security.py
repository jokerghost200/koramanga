import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional

# Stockage temporaire des tokens en mémoire (en production, utiliser Redis ou DB)
_temp_tokens = {}


def generate_secure_token(user_id: int, content_id: int, content_type: str = "manga") -> str:
    """
    Génère un token temporaire sécurisé pour accéder aux contenus protégés.
    Le token expire après 1 heure.
    """
    # Créer un token unique
    random_part = secrets.token_urlsafe(32)
    timestamp = datetime.now().timestamp()
    
    # Créer le hash
    data = f"{user_id}:{content_id}:{content_type}:{timestamp}:{random_part}"
    token = hashlib.sha256(data.encode()).hexdigest()[:64]
    
    # Stocker avec expiration
    _temp_tokens[token] = {
        "user_id": user_id,
        "content_id": content_id,
        "content_type": content_type,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=1)
    }
    
    return token


def verify_token(token: str) -> Optional[dict]:
    """
    Vérifie si un token est valide et n'a pas expiré.
    """
    if token not in _temp_tokens:
        return None
    
    token_data = _temp_tokens[token]
    
    # Vérifier l'expiration
    if datetime.now() > token_data["expires_at"]:
        del _temp_tokens[token]
        return None
    
    return token_data


def revoke_token(token: str) -> bool:
    """
    Révoque un token (pour la déconnexion ou déconnexion).
    """
    if token in _temp_tokens:
        del _temp_tokens[token]
        return True
    return False


def cleanup_expired_tokens():
    """
    Nettoie les tokens expirés (à appeler périodiquement).
    """
    now = datetime.now()
    expired = [t for t, data in _temp_tokens.items() if now > data["expires_at"]]
    for t in expired:
        del _temp_tokens[t]


def generate_watermark_text(user_id: int, username: str) -> str:
    """
    Génère le texte de watermark dynamique pour protéger les images.
    """
    return f"© KM Store - {username} (ID: {user_id}) - {datetime.now().strftime('%Y-%m-%d')}"


def get_secure_image_url(image_path: str, user_id: int, content_id: int) -> dict:
    """
    Génère une URL sécurisée pour une image avec token temporaire.
    """
    token = generate_secure_token(user_id, content_id, "image")
    
    return {
        "image_url": image_path,
        "token": token,
        "expires_in": 3600,  # 1 heure en secondes
        "watermark": generate_watermark_text(user_id, f"user_{user_id}")
    }


# En-têtes de sécurité pour la protection contre le piratage
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline'"
}


def get_security_headers() -> dict:
    """
    Retourne les en-têtes de sécurité pour protéger l'application.
    """
    return SECURITY_HEADERS

from fastapi import FastAPI
from database import engine, Base
from routers import auth, users, mangas, chapters, coins, donations, marketplace, security as security_router
import models

# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KM Store API",
    description="API pour KoraMangaStore - Plateforme Manga Africain et Marketplace Otaku",
    version="1.0.0"
)

# Enregistrer les routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(mangas.router)
app.include_router(chapters.router)
app.include_router(coins.router)
app.include_router(donations.router)
app.include_router(marketplace.router)
app.include_router(security_router.router)


@app.get("/")
def root():
    return {
        "message": "Bienvenue sur l'API KM Store",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

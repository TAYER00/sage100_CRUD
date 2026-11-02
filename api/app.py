"""
Application FastAPI : expose les fonctions CRUD Sage (crud/gestion_crud.py)
en endpoints REST/JSON.

Lancement (depuis la racine du projet, avec le venv 32 bits) :
    venv32\\Scripts\\python.exe -m uvicorn api.app:app --host 127.0.0.1 --port 8000

ou plus simplement :
    venv32\\Scripts\\python.exe main_api.py

Documentation interactive generee automatiquement par FastAPI, une fois
le serveur lance : http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import com_executor
from api.gestion_erreurs_http import enregistrer_gestionnaires_erreurs
from api.routes_entites import routeur as routeur_entites
from api.routes_sql import routeur as routeur_sql
from config.configuration import ConfigurationAPI

DOSSIER_INTERFACE = Path(__file__).resolve().parent.parent / "interface"


@asynccontextmanager
async def cycle_de_vie(app: FastAPI):
    """
    Cycle de vie de l'application : aucune ouverture de la connexion Sage
    au demarrage (pour que l'API reste joignable meme si Sage est
    momentanement indisponible - la connexion s'ouvre a la premiere
    requete qui en a besoin, voir api/com_executor.py). A l'arret, on
    ferme proprement la connexion Sage.
    """
    yield
    com_executor.fermer()


app = FastAPI(
    title="Sage Conex CRUD - API",
    description=(
        "API REST/JSON exposant les operations CRUD generiques sur les "
        "objets metiers Sage 100 (base Bijou SA). Voir "
        "00_analyse/04_VERIFICATION_COM.md pour le detail de l'API Sage "
        "reellement utilisee en arriere-plan."
    ),
    version="0.1.0",
    lifespan=cycle_de_vie,
)

# CORS : autorise les origines definies dans .env (API_ORIGINES_CORS),
# "*" par defaut pour le developpement local uniquement.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ConfigurationAPI.ORIGINES_AUTORISEES,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

enregistrer_gestionnaires_erreurs(app)
app.include_router(routeur_entites)
app.include_router(routeur_sql)


@app.get("/sante", tags=["technique"])
async def sante():
    """
    Objectif : verifier que l'API est en ligne.

    Ne teste PAS la connexion Sage (volontairement rapide et toujours
    disponible, meme si Sage est inaccessible) - pour verifier la
    connexion Sage reelle, appeler un endpoint /entites/... et regarder le
    code de retour (503 = Sage inaccessible).

    Retour : {"succes": true, "message": "API en ligne."}
    """
    return {"succes": True, "message": "API en ligne."}


# Interface web (voir interface/) : servie directement par ce serveur, sur
# la MEME origine que l'API - pas de CORS a gerer pour cette page, pas de
# second serveur a lancer. Monte EN DERNIER : les routes /sante et
# /entites/... definies ci-dessus restent prioritaires, seul ce qui ne
# correspond a aucune d'elles tombe sur les fichiers de interface/
# (html=True sert automatiquement index.html pour "/").
app.mount("/", StaticFiles(directory=DOSSIER_INTERFACE, html=True), name="interface")

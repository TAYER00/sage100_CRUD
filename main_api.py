"""
Point d'entree pour lancer la couche API HTTP (FastAPI/Uvicorn).

Usage (depuis la racine du projet sage_Conex_CRUD, avec le venv 32 bits) :
    venv32\\Scripts\\python.exe main_api.py

Documentation interactive une fois lance : http://127.0.0.1:8000/docs
"""

import uvicorn

from config.configuration import ConfigurationAPI

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host=ConfigurationAPI.HOTE,
        port=ConfigurationAPI.PORT,
        reload=False,  # le rechargement auto perturberait le thread COM dedie
    )

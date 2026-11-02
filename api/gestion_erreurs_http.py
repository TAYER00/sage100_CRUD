"""
Traduction des exceptions metier du projet (gestion_erreurs/exceptions.py)
en reponses HTTP/JSON. Chaque type d'erreur a un code HTTP dedie, pour que
le futur client web (ou tout consommateur de l'API) puisse distinguer une
erreur de validation d'une panne de connexion sans avoir a parser le texte
du message.

Format de reponse JSON commun a toutes les erreurs :
    {"succes": false, "type": "<NomDeLException>", "erreur": "<message>"}
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from gestion_erreurs.exceptions import (
    ErreurConnexion,
    ErreurEntiteInconnue,
    ErreurSDKSage,
    ErreurValidation,
)


def _reponse_erreur(code_http: int, erreur: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=code_http,
        content={
            "succes": False,
            "type": type(erreur).__name__,
            "erreur": str(erreur),
        },
    )


def enregistrer_gestionnaires_erreurs(app: FastAPI) -> None:
    """
    Objectif : enregistrer sur l'application FastAPI un gestionnaire par
    type d'erreur metier, avec le code HTTP correspondant :

        ErreurValidation     -> 400 Bad Request   (champ manquant, doublon,
                                 mode lecture seule, suppression non
                                 confirmee/non supportee...)
        ErreurEntiteInconnue  -> 404 Not Found     (entite absente du
                                 registre - ex: "/entites/xyz")
        ErreurConnexion       -> 503 Service Unavailable (Sage inaccessible)
        ErreurSDKSage         -> 502 Bad Gateway   (le SDK Sage lui-meme a
                                 refuse l'operation)
        Exception (generique) -> 500 Internal Server Error (bug imprevu)

    Parametres : app (FastAPI) - l'application sur laquelle enregistrer
    les gestionnaires.

    Retour : aucun (effet de bord sur app).
    """

    @app.exception_handler(ErreurValidation)
    async def _gerer_validation(request: Request, exc: ErreurValidation):
        return _reponse_erreur(400, exc)

    @app.exception_handler(ErreurEntiteInconnue)
    async def _gerer_entite_inconnue(request: Request, exc: ErreurEntiteInconnue):
        return _reponse_erreur(404, exc)

    @app.exception_handler(ErreurConnexion)
    async def _gerer_connexion(request: Request, exc: ErreurConnexion):
        return _reponse_erreur(503, exc)

    @app.exception_handler(ErreurSDKSage)
    async def _gerer_sdk_sage(request: Request, exc: ErreurSDKSage):
        return _reponse_erreur(502, exc)

    @app.exception_handler(Exception)
    async def _gerer_erreur_inattendue(request: Request, exc: Exception):
        return _reponse_erreur(500, exc)

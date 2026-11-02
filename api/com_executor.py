"""
Verrou COM : toutes les operations qui manipulent les objets metiers Sage
(COM, via pywin32/win32com) sont serialisees et executees sur le thread
PRINCIPAL du processus - jamais sur un thread secondaire.

IMPORTANT - constat verifie empiriquement sur ce poste (voir
00_analyse/04_VERIFICATION_COM.md pour le detail des tests) : l'appel
base.Open(...) de l'ActiveX Sage (CPTA.Base.18) reste BLOQUE
INDEFINIMENT lorsqu'il est invoque depuis un thread secondaire
(threading.Thread "a la main" ou concurrent.futures.ThreadPoolExecutor) -
meme en amorcant une file de messages Windows au prealable
(win32gui.PumpWaitingMessages). Seul le thread principal du processus
fonctionne de maniere fiable (verifie par plusieurs tests independants et
repetes). Ce n'est donc pas une negligence de pompage de messages : c'est
une contrainte reelle de ce composant COM, probablement herite de son
modele d'origine (application de bureau mono-thread).

Consequence du choix d'architecture : les appels Sage s'executent
directement sur le thread de la boucle asyncio d'Uvicorn (le thread
principal, en mode mono-processus/mono-worker - voir main_api.py), de
maniere synchrone et bloquante, proteges par un asyncio.Lock(). Pendant un
appel Sage, le serveur ne traite donc aucune autre requete HTTP en
parallele - choix delibere et documente, cohorent avec le fait que Sage
100 Objets Metiers n'est de toute facon pas concu pour un acces concurrent
multi-thread (voir aussi l'absence de SetDefault()/Factory par type
constatee dans la meme analyse).
"""

import asyncio
from typing import Any, Callable, Optional

from connexion.connexion_sage import ConnexionSage

_verrou = asyncio.Lock()
_connexion: Optional[ConnexionSage] = None


def _obtenir_connexion() -> ConnexionSage:
    """Donne une ConnexionSage ouverte, en l'ouvrant si besoin (une seule
    fois, reutilisee ensuite pour toute la duree de vie du serveur)."""
    global _connexion
    if _connexion is None or not _connexion.est_ouverte:
        _connexion = ConnexionSage()
        _connexion.ouvrir()
    return _connexion


async def executer(fonction: Callable, *args, **kwargs) -> Any:
    """
    Objectif : executer une fonction CRUD (qui attend une ConnexionSage en
    premier parametre, ex: crud.gestion_crud.lire) sous le verrou COM, en
    serialisant tous les appels Sage et en les executant sur le thread
    principal.

    Parametres :
        fonction : une fonction de crud/gestion_crud.py (lire, lister,
            creer, modifier, supprimer).
        *args, **kwargs : les arguments de cette fonction, SANS la
            connexion (fournie automatiquement par ce module).

    Retour : la valeur renvoyee par fonction(...).

    Erreurs possibles : toute exception levee par fonction() elle-meme
    (ErreurValidation, ErreurEntiteInconnue, ErreurSDKSage...) est
    propagee telle quelle a l'appelant - c'est la couche API (voir
    api/gestion_erreurs_http.py) qui la traduit en reponse HTTP.

    Exemple :
        resultat = await executer(lire, "tiers", "C001")
    """
    async with _verrou:
        connexion = _obtenir_connexion()
        return fonction(connexion, *args, **kwargs)


def fermer() -> None:
    """
    Objectif : fermer la connexion Sage a l'arret de l'application
    (voir api/app.py, cycle de vie "shutdown").
    """
    global _connexion
    if _connexion is not None:
        _connexion.fermer()
        _connexion = None

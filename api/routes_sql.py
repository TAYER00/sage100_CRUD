"""
Endpoints REST/JSON pour les requetes SQL predefinies, en lecture seule,
parametrees (voir connexion/requetes_sql_predefinies.py).

Ces requetes utilisent pyodbc (ConnexionSQLLectureSeule), PAS les objets
metiers COM - elles n'ont donc pas besoin du verrou COM
(api/com_executor.py) : chaque appel ouvre et ferme sa propre connexion
SQL Server (voir connexion/connexion_sql.py), ce qui est thread-safe.
L'execution est simplement deportee sur un thread via asyncio.to_thread
pour ne pas bloquer la boucle asyncio pendant l'appel reseau SQL Server.
"""

import asyncio
from typing import Any, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from connexion.requetes_sql_predefinies import REGISTRE_REQUETES, executer

routeur = APIRouter(prefix="/requetes-sql", tags=["requetes-sql"])


class CorpsExecution(BaseModel):
    """Corps JSON attendu pour POST /requetes-sql/{nom}/executer."""

    parametres: List[Any] = Field(
        ...,
        description="Une valeur par '?' de la requete, dans l'ordre.",
        examples=[["BAGUES"]],
    )


@routeur.get("")
async def lister_requetes():
    """
    Objectif : lister les requetes SQL predefinies disponibles, avec leurs
    parametres, pour que le Front-End genere un formulaire dynamique (un
    champ par parametre) sans connaitre le SQL a l'avance.

    Retour : {"succes": true, "requetes": {
        "<nom>": {"libelle": str, "description": str,
                  "parametres": [{"nom": str, "exemple": str}, ...]}
    }}

    Note : le texte SQL lui-meme n'est PAS renvoye au Front-End (il n'en a
    pas besoin - seuls le libelle et la liste des parametres le sont).
    """
    return {
        "succes": True,
        "requetes": {
            nom: {
                "libelle": infos["libelle"],
                "description": infos["description"],
                "parametres": infos["parametres"],
            }
            for nom, infos in REGISTRE_REQUETES.items()
        },
    }


@routeur.post("/{nom_requete}/executer")
async def executer_requete(nom_requete: str, corps: CorpsExecution):
    """
    Objectif : executer une requete SQL predefinie avec les valeurs de
    parametres fournies, en lecture seule.

    Parametres : nom_requete (str, dans l'URL), corps.parametres (liste de
    valeurs, une par "?", dans l'ordre).

    Retour : {"succes": true, "message": str, "resultats": list[dict]}.

    Erreurs possibles : 404 si la requete est inconnue
    (ErreurEntiteInconnue), 400 si le nombre de parametres est incorrect
    ou si un parametre est vide (ErreurValidation), 503 si la connexion
    SQL Server echoue (ErreurConnexion).

    Exemple :
        POST /requetes-sql/contacts_par_tiers/executer
        {"parametres": ["BAGUES"]}
    """
    resultats = await asyncio.to_thread(executer, nom_requete, corps.parametres)
    return {
        "succes": True,
        "message": f"[SUCCES] {len(resultats)} résultat(s) trouvé(s).",
        "resultats": resultats,
    }

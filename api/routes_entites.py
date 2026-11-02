"""
Endpoints REST/JSON exposant les fonctions CRUD generiques
(crud/gestion_crud.py) pour toutes les entites du registre
(crud/registre_entites.py - actuellement "tiers").

Convention REST :
    GET    /entites                      -> entites connues
    GET    /entites/{entite}             -> lister() (pagine)
    GET    /entites/{entite}/{id}        -> lire()
    POST   /entites/{entite}             -> creer()
    PUT    /entites/{entite}/{id}        -> modifier()
    DELETE /entites/{entite}/{id}        -> supprimer()

Toutes les operations qui touchent Sage passent par
api.com_executor.executer(...) (le "verrou COM") - aucun appel direct a
une fonction de crud/gestion_crud.py ni a connexion_sage.py ici.
"""

from fastapi import APIRouter, Query

from api import com_executor
from api.schemas import CorpsCreation, CorpsModification
from crud.gestion_crud import creer, lire, lister, modifier, supprimer
from crud.registre_entites import REGISTRE_ENTITES

routeur = APIRouter(prefix="/entites", tags=["entites"])


@routeur.get("")
async def entites_connues():
    """
    Objectif : lister les noms d'entites prises en charge par l'API.

    Retour : {"succes": true, "entites": ["tiers", ...]}.
    """
    return {"succes": True, "entites": sorted(REGISTRE_ENTITES)}


@routeur.get("/{entite}")
async def lister_entite(
    entite: str,
    page: int = Query(1, ge=1, description="Numero de page (commence a 1)."),
    taille_page: int = Query(20, ge=1, le=200, description="Nombre d'elements par page (max 200)."),
):
    """
    Objectif : lister les enregistrements d'une entite, avec pagination.

    Parametres :
        entite (str) : nom de l'entite (ex: "tiers").
        page (int) : numero de page demandee, >= 1.
        taille_page (int) : nombre de resultats par page, 1 a 200.

    Retour : {"succes": true, "message": str, "page": int,
        "taille_page": int, "total": int, "nombre_pages": int,
        "resultats": list[dict]}.

    Erreurs possibles : 404 si l'entite est inconnue (ErreurEntiteInconnue),
    502 si le SDK Sage echoue (ErreurSDKSage) - voir
    api/gestion_erreurs_http.py.

    Exemple : GET /entites/tiers?page=2&taille_page=10
    """
    resultat = await com_executor.executer(lister, entite)
    tous_les_resultats = resultat["resultats"]
    total = len(tous_les_resultats)

    debut = (page - 1) * taille_page
    fin = debut + taille_page
    page_resultats = tous_les_resultats[debut:fin]
    nombre_pages = max(1, -(-total // taille_page))  # arrondi au superieur

    return {
        "succes": True,
        "message": resultat["message"],
        "page": page,
        "taille_page": taille_page,
        "total": total,
        "nombre_pages": nombre_pages,
        "resultats": page_resultats,
    }


@routeur.get("/{entite}/champs")
async def champs_formulaire_entite(entite: str):
    """
    Objectif : decrire les champs du formulaire de creation/modification
    d'une entite, pour que le Front-End genere des champs de saisie
    adaptes (ComboBox pour les champs a choix fixe comme CT_Type, champs
    texte avec exemple/suggestions pour les autres) plutot qu'une zone de
    texte libre.

    Ne touche pas Sage/COM - lit uniquement le registre Python
    (crud/registre_entites.py), donc toujours rapide, sans verrou COM.

    Parametres : entite (str, dans l'URL).

    Retour : {"succes": true, "champ_cle": str,
        "champs": [{"nom": str, "libelle": str, "type": "texte"|"liste",
                     "obligatoire": bool, "exemple": str (optionnel),
                     "suggestions": list (optionnel),
                     "options": [{"valeur": ..., "libelle": str}] (si type="liste")}]}.

    Erreurs possibles : 404 si entite inconnue (ErreurEntiteInconnue).

    Exemple : GET /entites/tiers/champs
    """
    from crud.registre_entites import metadonnees

    infos = metadonnees(entite)
    return {
        "succes": True,
        "champ_cle": infos["champ_cle"],
        "champs": infos.get("champs_formulaire", []),
    }


@routeur.get("/{entite}/{identifiant}")
async def lire_entite(entite: str, identifiant: str):
    """
    Objectif : lire un enregistrement par son identifiant.

    Parametres : entite (str), identifiant (str, dans l'URL).

    Retour : {"succes": true, "message": str, "donnees": dict}.

    Erreurs possibles : 400 si identifiant/entite inexistant
    (ErreurValidation), 404 si entite inconnue du registre
    (ErreurEntiteInconnue), 502 si echec SDK Sage (ErreurSDKSage).

    Exemple : GET /entites/tiers/C001
    """
    return await com_executor.executer(lire, entite, identifiant)


@routeur.post("/{entite}", status_code=201)
async def creer_entite(entite: str, corps: CorpsCreation):
    """
    Objectif : creer un nouvel enregistrement.

    Parametres : entite (str), corps (CorpsCreation) - voir api/schemas.py.

    Retour (201 Created) : {"succes": true, "message": str, "cle": str}.

    Erreurs possibles : 400 si champ obligatoire manquant/doublon/mode
    lecture seule actif (ErreurValidation), 404 si entite inconnue, 502 si
    echec SDK Sage.

    Exemple :
        POST /entites/tiers
        {"donnees": {"CT_Num": "C001", "CT_Intitule": "Client Test",
                      "CT_Type": 0, "CG_NumPrinc": "4110000"}}
    """
    return await com_executor.executer(creer, entite, corps.donnees)


@routeur.put("/{entite}/{identifiant}")
async def modifier_entite(entite: str, identifiant: str, corps: CorpsModification):
    """
    Objectif : modifier un enregistrement existant.

    Parametres : entite (str), identifiant (str), corps (CorpsModification).

    Retour : {"succes": true, "message": str}.

    Erreurs possibles : 400 si enregistrement introuvable/aucune donnee
    fournie/mode lecture seule actif, 404 si entite inconnue, 502 si echec
    SDK Sage.

    Exemple :
        PUT /entites/tiers/C001
        {"donnees": {"CT_Intitule": "Client Modifie"}}
    """
    return await com_executor.executer(modifier, entite, identifiant, corps.donnees)


@routeur.delete("/{entite}/{identifiant}")
async def supprimer_entite(
    entite: str,
    identifiant: str,
    confirmer: bool = Query(False, description="Doit valoir true pour confirmer la suppression."),
):
    """
    Objectif : supprimer un enregistrement existant.

    Parametres : entite (str), identifiant (str), confirmer (bool, query
        param - doit etre explicitement true).

    Retour : {"succes": true, "message": str}.

    Erreurs possibles : 400 si confirmer=false, si l'entite ne supporte pas
    la suppression (ex: "tiers", aucun Remove() disponible dans l'API Sage
    installee - voir 00_analyse/04_VERIFICATION_COM.md), ou si
    l'enregistrement n'existe pas. 404 si entite inconnue. 502 si echec SDK
    Sage.

    Exemple : DELETE /entites/tiers/C001?confirmer=true
    """
    return await com_executor.executer(supprimer, entite, identifiant, confirmer)

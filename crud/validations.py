"""
Validations communes a toutes les operations CRUD (prompt_2.txt section 6) :
connexion active, identifiant obligatoire, champs obligatoires, mode
lecture seule. Chaque fonction leve ErreurValidation avec un message
"[VALIDATION] ..." en francais des qu'une regle n'est pas respectee.
"""

from gestion_erreurs.exceptions import ErreurValidation


def valider_connexion_ouverte(connexion):
    """
    Objectif : s'assurer que la connexion Sage est ouverte avant toute
    operation CRUD.

    Parametres : connexion (ConnexionSage ou ConnexionSQLLectureSeule).

    Retour : aucun.

    Erreurs possibles : ErreurValidation si connexion.est_ouverte vaut False.
    """
    if not getattr(connexion, "est_ouverte", False):
        raise ErreurValidation(
            "[VALIDATION] La connexion a Sage n'est pas ouverte."
        )


def valider_identifiant(identifiant, champ_cle: str):
    """
    Objectif : verifier que l'identifiant (cle primaire) est renseigne.

    Parametres :
        identifiant : la valeur fournie par l'appelant.
        champ_cle (str) : nom du champ cle, pour un message clair.

    Retour : aucun.

    Erreurs possibles : ErreurValidation si l'identifiant est vide/None.
    """
    if identifiant is None or not str(identifiant).strip():
        raise ErreurValidation(
            f"[VALIDATION] Le champ '{champ_cle}' (cle) est obligatoire."
        )


def valider_champs_obligatoires(donnees: dict, champs_obligatoires: list):
    """
    Objectif : verifier que tous les champs obligatoires d'une entite sont
    presents et non vides dans les donnees fournies.

    Parametres :
        donnees (dict) : champs fournis par l'appelant.
        champs_obligatoires (list[str]) : noms des champs requis.

    Retour : aucun.

    Erreurs possibles : ErreurValidation listant les champs manquants.

    Note : un champ dont la valeur vaut 0 (ex: CT_Type=0 pour "Client")
    est bien considere comme PRESENT - seules une cle absente, une valeur
    None, ou une chaine vide/blanche sont considerees comme manquantes.
    """
    manquants = [
        champ
        for champ in champs_obligatoires
        if champ not in donnees
        or donnees[champ] is None
        or str(donnees[champ]).strip() == ""
    ]
    if manquants:
        raise ErreurValidation(
            f"[VALIDATION] Champ(s) obligatoire(s) manquant(s) : "
            f"{', '.join(manquants)}."
        )


def valider_mode_ecriture_autorise():
    """
    Objectif : refuser toute ecriture (creer/modifier/supprimer) quand le
    mode lecture seule est actif (prompt_2.txt section 8 : "Prevoir un
    mode lecture seule pour les premiers tests").

    Retour : aucun.

    Erreurs possibles : ErreurValidation si MODE_LECTURE_SEULE=true.
    """
    from config.configuration import mode_lecture_seule_actif

    if mode_lecture_seule_actif():
        raise ErreurValidation(
            "[VALIDATION] Mode lecture seule actif (MODE_LECTURE_SEULE=true "
            "dans .env) : creation, modification et suppression sont "
            "desactivees. Passez MODE_LECTURE_SEULE=false pour les activer."
        )


def valider_suppression_confirmee(confirmer: bool):
    """
    Objectif : exiger une confirmation explicite avant toute suppression
    (prompt_2.txt section 8 : "Prevoir une confirmation avant chaque
    suppression").

    Parametres : confirmer (bool) - doit valoir True pour continuer.

    Retour : aucun.

    Erreurs possibles : ErreurValidation si confirmer est False.
    """
    if not confirmer:
        raise ErreurValidation(
            "[VALIDATION] Suppression non confirmee : passez confirmer=True "
            "pour confirmer explicitement cette suppression."
        )

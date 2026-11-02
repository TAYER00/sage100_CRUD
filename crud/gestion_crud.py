"""
Fonctions CRUD generiques en francais : creer(), lire(), modifier(),
supprimer(), lister().

Une seule implementation pour toutes les entites, pilotee par le registre
declaratif de crud/registre_entites.py - conformement a prompt_2.txt
section 4 et au principe confirme dans docs/sage_objet_metier.docx :
"Le code CRUD est standard et reutilisable : seuls changent le nom de la
factory, la cle de lecture, et les champs selon l'objet."

Chaque fonction recoit une connexion Sage DEJA OUVERTE (voir
connexion/connexion_sage.py) : ces fonctions ne gerent pas l'ouverture/
fermeture de la connexion, seulement le cycle de vie des objets Sage
qu'elles manipulent (prompt_2.txt section 7).

Correspondance avec le cycle de vie Sage (voir docs/sage_objet_metier.docx
et 00_analyse/04_VERIFICATION_COM.md pour la version reellement installee) :
    CREATE = collection.AddNew() + affectation des champs + objet.Write()
    READ   = base.<LireParCle>(identifiant)
    UPDATE = READ + affectation des champs + objet.Write()
    DELETE = READ + objet.Remove() (si l'entite le supporte)
    LISTER = parcours de la collection (Factory)

Regle absolue (prompt_2.txt section 6) : un message [SUCCES] n'est jamais
renvoye avant une relecture de controle confirmant que Sage a bien
persiste l'operation.
"""

from crud.registre_entites import metadonnees
from crud.validations import (
    valider_champs_obligatoires,
    valider_connexion_ouverte,
    valider_identifiant,
    valider_mode_ecriture_autorise,
    valider_suppression_confirmee,
)
from gestion_erreurs.exceptions import (
    ErreurSDKSage,
    ErreurValidation,
    message_succes,
)


def creer(connexion, entite: str, donnees: dict) -> dict:
    """
    Objectif : creer un nouvel enregistrement Sage pour l'entite donnee.

    Parametres :
        connexion : une ConnexionSage deja ouverte (connexion.ouvrir()).
        entite (str) : nom de l'entite dans le registre (ex: "tiers").
        donnees (dict) : champs a renseigner, doit inclure le champ cle
            de l'entite (ex: {"CT_Num": "C001", "CT_Intitule": "Client Test"}).

    Retour : dict {"succes": True, "message": str, "cle": valeur de la cle}.

    Validations effectuees :
        - connexion ouverte,
        - mode lecture seule desactive,
        - entite connue dans le registre,
        - champs obligatoires de l'entite presents et non vides,
        - l'enregistrement ne doit pas deja exister (pas de doublon).

    Erreurs possibles :
        ErreurValidation (champ manquant, doublon, mode lecture seule),
        ErreurEntiteInconnue (entite absente du registre),
        ErreurSDKSage (le SDK Sage a refuse l'ecriture, ou la relecture de
        controle ne confirme pas la creation).

    Exemple :
        creer(connexion, "tiers", {"CT_Num": "C001", "CT_Intitule": "Client Test"})
    """
    valider_connexion_ouverte(connexion)
    valider_mode_ecriture_autorise()
    infos = metadonnees(entite)

    valider_champs_obligatoires(donnees, infos["champs_obligatoires"])
    cle = donnees.get(infos["champ_cle"])
    valider_identifiant(cle, infos["champ_cle"])

    base = connexion.base_comptable

    # Detection de doublon : l'enregistrement ne doit pas deja exister.
    if infos["lire_par_cle"](base, cle) is not None:
        raise ErreurValidation(
            f"[VALIDATION] Un(e) {infos['libelle']} avec la cle '{cle}' "
            f"existe deja."
        )

    objet = None
    try:
        collection = infos["obtenir_collection"](base)
        objet = collection.AddNew()
        for champ, valeur in donnees.items():
            setattr(objet, champ, valeur)
        objet.Write()
    except ErreurValidation:
        raise
    except Exception as erreur:
        raise ErreurSDKSage(
            f"[ERREUR] Echec Sage lors de la creation ({infos['libelle']}) : "
            f"{erreur}"
        ) from erreur
    finally:
        # Liberation de la reference a l'objet COM une fois l'ecriture
        # tentee (prompt_2.txt section 7) - on ne retourne jamais l'objet
        # COM lui-meme a l'appelant, seulement un dictionnaire (voir
        # _vers_dictionnaire plus bas).
        objet = None

    # Jamais de [SUCCES] sans confirmation reelle par relecture.
    confirmation = infos["lire_par_cle"](base, cle)
    if confirmation is None:
        raise ErreurSDKSage(
            f"[ERREUR] La creation de '{cle}' n'a pas pu etre confirmee "
            f"par relecture - l'operation a peut-etre echoue silencieusement."
        )

    return {
        "succes": True,
        "message": message_succes(
            f"{infos['libelle'].capitalize()} '{cle}' cree avec succes."
        ),
        "cle": cle,
    }


def lire(connexion, entite: str, identifiant) -> dict:
    """
    Objectif : lire un enregistrement Sage existant par sa cle.

    Parametres :
        connexion : une ConnexionSage deja ouverte.
        entite (str) : nom de l'entite dans le registre.
        identifiant : valeur de la cle primaire (ex: "C001").

    Retour : dict {"succes": True, "message": str, "donnees": dict des
        champs lus (voir champs_lecture du registre)}.

    Validations effectuees :
        - connexion ouverte,
        - entite connue,
        - identifiant non vide,
        - l'enregistrement doit exister.

    Erreurs possibles :
        ErreurValidation (identifiant manquant, enregistrement introuvable),
        ErreurEntiteInconnue, ErreurSDKSage (echec cote SDK Sage).

    Exemple :
        lire(connexion, "tiers", "C001")
    """
    valider_connexion_ouverte(connexion)
    infos = metadonnees(entite)
    valider_identifiant(identifiant, infos["champ_cle"])

    base = connexion.base_comptable
    try:
        objet = infos["lire_par_cle"](base, identifiant)
    except Exception as erreur:
        raise ErreurSDKSage(
            f"[ERREUR] Echec Sage lors de la lecture ({infos['libelle']}) : "
            f"{erreur}"
        ) from erreur

    if objet is None:
        raise ErreurValidation(
            f"[ERREUR] Le {infos['libelle']} '{identifiant}' n'existe pas."
        )

    donnees_lues = _vers_dictionnaire(objet, infos)
    objet = None  # liberation de la reference COM, la copie est deja faite

    return {
        "succes": True,
        "message": message_succes(
            f"{infos['libelle'].capitalize()} '{identifiant}' lu avec succes."
        ),
        "donnees": donnees_lues,
    }


def modifier(connexion, entite: str, identifiant, donnees: dict) -> dict:
    """
    Objectif : modifier un enregistrement Sage existant.

    Parametres :
        connexion : une ConnexionSage deja ouverte.
        entite (str) : nom de l'entite dans le registre.
        identifiant : valeur de la cle primaire de l'enregistrement a modifier.
        donnees (dict) : champs a modifier, ex: {"CT_Intitule": "Nouveau nom"}.

    Retour : dict {"succes": True, "message": str}.

    Validations effectuees :
        - connexion ouverte,
        - mode lecture seule desactive,
        - entite connue, identifiant non vide,
        - au moins un champ a modifier est fourni,
        - l'enregistrement doit exister avant modification.

    Erreurs possibles :
        ErreurValidation (identifiant/donnees manquants, enregistrement
        introuvable, mode lecture seule), ErreurEntiteInconnue,
        ErreurSDKSage (echec cote SDK Sage, ou relecture de controle ne
        confirme pas la modification).

    Exemple :
        modifier(connexion, "tiers", "C001", {"CT_Intitule": "Client Modifie"})
    """
    valider_connexion_ouverte(connexion)
    valider_mode_ecriture_autorise()
    infos = metadonnees(entite)
    valider_identifiant(identifiant, infos["champ_cle"])

    if not donnees:
        raise ErreurValidation(
            "[VALIDATION] Aucune donnee a modifier n'a ete fournie."
        )

    base = connexion.base_comptable
    objet = None
    try:
        objet = infos["lire_par_cle"](base, identifiant)
        if objet is None:
            raise ErreurValidation(
                f"[ERREUR] Le {infos['libelle']} '{identifiant}' n'existe pas."
            )
        for champ, valeur in donnees.items():
            setattr(objet, champ, valeur)
        objet.Write()
    except ErreurValidation:
        raise
    except Exception as erreur:
        raise ErreurSDKSage(
            f"[ERREUR] Echec Sage lors de la modification ({infos['libelle']}) : "
            f"{erreur}"
        ) from erreur
    finally:
        objet = None

    # Relecture de controle : chaque champ modifie doit correspondre a la
    # valeur demandee avant d'annoncer un succes.
    confirmation = infos["lire_par_cle"](base, identifiant)
    champs_corrects = confirmation is not None and all(
        str(getattr(confirmation, champ, None)) == str(valeur)
        for champ, valeur in donnees.items()
    )
    if not champs_corrects:
        raise ErreurSDKSage(
            f"[ERREUR] La modification de '{identifiant}' n'a pas pu etre "
            f"confirmee par relecture."
        )

    return {
        "succes": True,
        "message": message_succes(
            f"{infos['libelle'].capitalize()} '{identifiant}' modifie avec succes."
        ),
    }


def supprimer(connexion, entite: str, identifiant, confirmer: bool = False) -> dict:
    """
    Objectif : supprimer un enregistrement Sage existant.

    Parametres :
        connexion : une ConnexionSage deja ouverte.
        entite (str) : nom de l'entite dans le registre.
        identifiant : valeur de la cle primaire de l'enregistrement a supprimer.
        confirmer (bool) : doit valoir True - confirmation explicite
            obligatoire avant toute suppression (prompt_2.txt section 8).

    Retour : dict {"succes": True, "message": str}.

    Validations effectuees :
        - connexion ouverte,
        - mode lecture seule desactive,
        - entite connue, identifiant non vide,
        - suppression confirmee explicitement (confirmer=True),
        - l'entite doit supporter la suppression (voir
          registre_entites.REGISTRE_ENTITES[...]["suppression_supportee"] -
          par exemple, les tiers ne la supportent pas, voir
          00_analyse/04_VERIFICATION_COM.md : aucune methode Remove()
          trouvee dans l'API COM reellement installee),
        - l'enregistrement doit exister.

    Erreurs possibles :
        ErreurValidation (confirmation manquante, entite introuvable,
        suppression non supportee par cette entite, mode lecture seule),
        ErreurEntiteInconnue, ErreurSDKSage (echec cote SDK Sage, ou la
        relecture de controle montre que l'enregistrement existe toujours).

    Exemple :
        supprimer(connexion, "tiers", "C001", confirmer=True)
        # -> leve ErreurValidation : suppression non supportee pour "tiers"
    """
    valider_connexion_ouverte(connexion)
    valider_mode_ecriture_autorise()
    infos = metadonnees(entite)
    valider_identifiant(identifiant, infos["champ_cle"])
    valider_suppression_confirmee(confirmer)

    if not infos.get("suppression_supportee", False):
        raise ErreurValidation(
            f"[VALIDATION] La suppression n'est pas prise en charge pour "
            f"l'entite '{entite}' (aucune methode Remove() disponible dans "
            f"le SDK Sage installe sur ce poste - voir "
            f"00_analyse/04_VERIFICATION_COM.md)."
        )

    base = connexion.base_comptable
    objet = None
    try:
        objet = infos["lire_par_cle"](base, identifiant)
        if objet is None:
            raise ErreurValidation(
                f"[ERREUR] Le {infos['libelle']} '{identifiant}' n'existe pas."
            )
        objet.Remove()
    except ErreurValidation:
        raise
    except Exception as erreur:
        raise ErreurSDKSage(
            f"[ERREUR] Echec Sage lors de la suppression ({infos['libelle']}) : "
            f"{erreur}"
        ) from erreur
    finally:
        objet = None

    confirmation = infos["lire_par_cle"](base, identifiant)
    if confirmation is not None:
        raise ErreurSDKSage(
            f"[ERREUR] La suppression de '{identifiant}' n'a pas pu etre "
            f"confirmee : l'enregistrement existe toujours."
        )

    return {
        "succes": True,
        "message": message_succes(
            f"{infos['libelle'].capitalize()} '{identifiant}' supprime avec succes."
        ),
    }


def lister(connexion, entite: str) -> dict:
    """
    Objectif : lister tous les enregistrements Sage d'une entite.

    Parametres :
        connexion : une ConnexionSage deja ouverte.
        entite (str) : nom de l'entite dans le registre.

    Retour : dict {"succes": True, "message": str, "resultats": list[dict]}.

    Validations effectuees : connexion ouverte, entite connue.

    Erreurs possibles : ErreurEntiteInconnue, ErreurSDKSage (echec cote
    SDK Sage lors du parcours de la collection).

    Exemple :
        lister(connexion, "tiers")
    """
    valider_connexion_ouverte(connexion)
    infos = metadonnees(entite)

    base = connexion.base_comptable
    try:
        collection = infos["obtenir_collection"](base)
        resultats = [
            _vers_dictionnaire(collection.Item(i), infos)
            for i in range(1, collection.Count + 1)
        ]
    except Exception as erreur:
        raise ErreurSDKSage(
            f"[ERREUR] Echec Sage lors du listage ({infos['libelle']}) : "
            f"{erreur}"
        ) from erreur

    return {
        "succes": True,
        "message": message_succes(
            f"{len(resultats)} {infos['libelle']}(s) trouve(s)."
        ),
        "resultats": resultats,
    }


def _vers_dictionnaire(objet, infos: dict) -> dict:
    """
    Convertit un objet COM Sage en dictionnaire Python simple.

    Ne renvoie jamais l'objet COM lui-meme a l'appelant, pour eviter tout
    risque d'utilisation d'une reference COM apres liberation
    (prompt_2.txt section 7).
    """
    champs = infos.get("champs_lecture") or [infos["champ_cle"]]
    return {champ: getattr(objet, champ, None) for champ in champs}

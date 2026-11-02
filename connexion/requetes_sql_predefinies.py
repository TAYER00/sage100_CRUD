"""
Registre des requetes SQL predefinies, en LECTURE SEULE, parametrees.

Objectif : permettre au Front-End de generer dynamiquement un champ de
saisie par parametre ("?") d'une requete SQL donnee, sans jamais coder en
dur un formulaire specifique a une requete - exactement comme
crud/registre_entites.py evite une fonction par entite, ce module evite
une route/un formulaire par requete SQL.

Securite (prompt_2.txt section 8) : les valeurs saisies par l'utilisateur
ne sont JAMAIS inserees directement dans le texte SQL. Elles passent
toujours par les parametres positionnels ("?") de pyodbc (voir
connexion/connexion_sql.py, ConnexionSQLLectureSeule.executer_lecture) -
la meme requete preparee est executee avec des valeurs differentes, ce qui
elimine tout risque d'injection SQL.

Pour ajouter une nouvelle requete : ajouter une entree a REGISTRE_REQUETES
avec son libelle, son SQL (un "?" par parametre, dans l'ordre) et la liste
des parametres (un dict par "?", dans le MEME ordre que les "?").
"""

REGISTRE_REQUETES = {
    "contacts_par_tiers": {
        "libelle": "Contacts d'un tiers",
        "description": "Liste les contacts (F_CONTACTT) d'un tiers, par son code.",
        "sql": (
            "SELECT CT_Num AS [Code tiers], CT_No AS [N° contact], "
            "CT_Nom AS [Nom], CT_Prenom AS [Prénom] "
            "FROM dbo.F_CONTACTT WHERE CT_Num = ? ORDER BY CT_No"
        ),
        "parametres": [
            {"nom": "Code tiers", "exemple": "BAGUES"},
        ],
    },
    "tiers_par_ville": {
        "libelle": "Tiers d'une ville",
        "description": "Liste les tiers (F_COMPTET) situes dans une ville donnee.",
        "sql": (
            "SELECT CT_Num AS [Code tiers], CT_Intitule AS [Intitulé], "
            "CT_Type AS [Type], CT_Ville AS [Ville] "
            "FROM dbo.F_COMPTET WHERE CT_Ville = ? ORDER BY CT_Num"
        ),
        "parametres": [
            {"nom": "Ville", "exemple": "Metz"},
        ],
    },
}


def metadonnees(nom_requete: str) -> dict:
    """
    Objectif : recuperer la definition d'une requete SQL predefinie.

    Parametres : nom_requete (str) - cle du registre.

    Retour : dict {"libelle", "description", "sql", "parametres"}.

    Erreurs possibles : ErreurEntiteInconnue si nom_requete est absent du
    registre.
    """
    from gestion_erreurs.exceptions import ErreurEntiteInconnue

    if nom_requete not in REGISTRE_REQUETES:
        raise ErreurEntiteInconnue(
            f"[ERREUR] La requete '{nom_requete}' n'est pas definie. "
            f"Requetes connues : {', '.join(REGISTRE_REQUETES) or 'aucune'}."
        )
    return REGISTRE_REQUETES[nom_requete]


def executer(nom_requete: str, valeurs_parametres: list) -> list:
    """
    Objectif : executer une requete SQL predefinie avec les valeurs de
    parametres fournies par l'appelant (Front-End), en lecture seule.

    Parametres :
        nom_requete (str) : cle du registre (ex: "contacts_par_tiers").
        valeurs_parametres (list) : une valeur par "?" de la requete,
            DANS L'ORDRE - jamais inseree directement dans le texte SQL,
            toujours transmise comme parametre pyodbc (voir
            connexion/connexion_sql.py).

    Retour : liste de dictionnaires (une ligne de resultat par entree).

    Validations effectuees : la requete doit exister dans le registre, et
    le nombre de valeurs fournies doit correspondre exactement au nombre
    de parametres attendus.

    Erreurs possibles : ErreurEntiteInconnue (requete inconnue),
    ErreurValidation (nombre de parametres incorrect), ErreurConnexion
    (echec SQL Server, voir connexion_sql.py).

    Exemple :
        executer("contacts_par_tiers", ["BAGUES"])
    """
    from gestion_erreurs.exceptions import ErreurValidation

    infos = metadonnees(nom_requete)
    attendus = infos["parametres"]

    if len(valeurs_parametres) != len(attendus):
        raise ErreurValidation(
            f"[VALIDATION] La requete '{nom_requete}' attend "
            f"{len(attendus)} parametre(s) ({', '.join(p['nom'] for p in attendus)}), "
            f"{len(valeurs_parametres)} fourni(s)."
        )

    for valeur, definition in zip(valeurs_parametres, attendus):
        if valeur is None or not str(valeur).strip():
            raise ErreurValidation(
                f"[VALIDATION] Le paramètre '{definition['nom']}' est obligatoire."
            )

    from connexion.connexion_sql import ConnexionSQLLectureSeule

    connexion = ConnexionSQLLectureSeule()
    return connexion.executer_lecture(infos["sql"], valeurs_parametres)

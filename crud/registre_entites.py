"""
Registre declaratif des entites prises en charge par les fonctions CRUD
generiques de gestion_crud.py.

Principe directeur (demande par prompt_2.txt section 4, et confirme
textuellement dans docs/sage_objet_metier.docx : "Le code CRUD est
standard et reutilisable : seuls changent le nom de la factory, la cle de
lecture, et les champs selon l'objet") : UNE seule implementation de
creer()/lire()/modifier()/supprimer()/lister() dans gestion_crud.py,
pilotee par ces metadonnees - jamais une fonction differente par table.

ATTENTION - les noms Sage ci-dessous sont ceux de l'API COM REELLEMENT
verifiee sur ce poste (voir 00_analyse/04_VERIFICATION_COM.md), pas les
noms generiques "Application.FactoryXxx.Read()/.Create()" utilises a
titre pedagogique dans le docx. L'API reelle (ProgID CPTA.Base.18) expose
un nom de methode de lecture different par entite (ex: ReadCompteTNumero)
porte par l'objet "Base" directement, pas une methode .Read() unique sur
un objet "Factory" separe - et n'a PAS de methode Create()/WriteDefault()
distincte : la creation passe par collection.AddNew() + objet.Write().
"""


def _collection_tiers(base):
    """'Factory' des tiers : la collection CompteTs de la base comptable."""
    return base.CompteTs


def _lire_tiers(base, cle):
    """Lecture d'un tiers par sa cle primaire (CT_Num)."""
    return base.ReadCompteTNumero(cle)


# Champs lus/exposes pour un tiers (lire()/lister()) - sous-ensemble verifie
# dans 00_analyse/04_VERIFICATION_COM.md (interface ICPTACompteT8).
CHAMPS_LECTURE_TIERS = [
    "CT_Num",
    "CT_Intitule",
    "CT_Type",
    "CT_Adresse",
    "CT_CodePostal",
    "CT_Ville",
    "CT_Pays",
    "CT_Telephone",
    "CT_EMail",
]

REGISTRE_ENTITES = {
    "tiers": {
        "libelle": "tiers",
        "champ_cle": "CT_Num",
        "obtenir_collection": _collection_tiers,
        "lire_par_cle": _lire_tiers,
        # CT_Type et CG_NumPrinc sont obligatoires EN PRATIQUE sur cette
        # API (confirme par un test d'ecriture reel - voir
        # 00_analyse/04_VERIFICATION_COM.md) : l'API COM installee ici
        # (CPTA.Base.18) n'a pas de SetDefault()/Factory par type pour les
        # deriver automatiquement, contrairement a l'API IBO* documentee
        # dans le PDF Objets Metiers. Sans eux, .Write() echoue avec
        # l'erreur Sage "Probleme a l'ecriture d'un enregistrement dans le
        # fichier comptes de tiers !" (code -9016).
        "champs_obligatoires": ["CT_Num", "CT_Intitule", "CT_Type", "CG_NumPrinc"],
        "champs_lecture": CHAMPS_LECTURE_TIERS,
        # Aucune methode Remove() trouvee pour les tiers dans l'API COM
        # reelle (ni sur l'objet, ni sur sa collection) - voir
        # 00_analyse/04_VERIFICATION_COM.md. supprimer() refusera donc
        # systematiquement cette entite tant que ce n'est pas infirme.
        "suppression_supportee": False,
    },
    # "article", "famille", "document_vente" : pas encore ajoutes - en
    # attente de la disponibilite d'une API COM Gestion Commerciale sur ce
    # poste (voir 00_analyse/03_QUESTIONS_OUVERTES.md point 6).
}


def entite_connue(entite: str) -> bool:
    """Indique si l'entite est presente dans le registre."""
    return entite in REGISTRE_ENTITES


def metadonnees(entite: str) -> dict:
    """
    Objectif : recuperer les metadonnees d'une entite du registre.

    Parametres : entite (str) - cle du registre (ex: "tiers").

    Retour : dict de metadonnees (factory, cle, champs...).

    Erreurs possibles : ErreurEntiteInconnue si l'entite n'existe pas dans
    le registre.
    """
    from gestion_erreurs.exceptions import ErreurEntiteInconnue

    if entite not in REGISTRE_ENTITES:
        raise ErreurEntiteInconnue(
            f"[ERREUR] L'entite '{entite}' n'est pas prise en charge. "
            f"Entites connues : {', '.join(REGISTRE_ENTITES) or 'aucune'}."
        )
    return REGISTRE_ENTITES[entite]

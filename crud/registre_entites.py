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

# Description des champs du formulaire de creation/modification, pour que
# le Front-End genere des champs de saisie adaptes (ComboBox pour CT_Type,
# exemples de valeurs pour guider la saisie) plutot qu'une zone de texte
# libre - voir api/routes_entites.py (GET /entites/{entite}/champs) et
# interface/app.js. CT_Type=0/1/2/3 confirme dans
# 00_analyse/01_ANALYSE_DOCUMENTATION.md (table F_COMPTET).
CHAMPS_FORMULAIRE_TIERS = [
    {
        "nom": "CT_Num",
        "libelle": "Code tiers",
        "type": "texte",
        "exemple": "FOUR01",
        "obligatoire": True,
    },
    {
        "nom": "CT_Intitule",
        "libelle": "Intitulé",
        "type": "texte",
        "exemple": "Fournisseur Test",
        "obligatoire": True,
    },
    {
        "nom": "CT_Type",
        "libelle": "Type de tiers",
        "type": "liste",
        "options": [
            {"valeur": 0, "libelle": "Client"},
            {"valeur": 1, "libelle": "Fournisseur"},
            {"valeur": 2, "libelle": "Salarié"},
            {"valeur": 3, "libelle": "Autre"},
        ],
        "obligatoire": True,
    },
    {
        "nom": "CG_NumPrinc",
        "libelle": "Compte général lié",
        "type": "texte",
        # Exemples reels observes sur des tiers existants de Bijou SA
        # (voir 00_analyse/04_VERIFICATION_COM.md) - un client/fournisseur
        # doit etre rattache a un compte general EXISTANT (F_COMPTEG).
        "suggestions": ["4110000", "4010000", "4040000"],
        "exemple": "4110000 (clients) / 4010000 (fournisseurs)",
        "obligatoire": True,
    },
    {
        "nom": "CT_Adresse",
        "libelle": "Adresse",
        "type": "texte",
        "exemple": "12 rue des Lilas",
        "obligatoire": False,
    },
    {
        "nom": "CT_CodePostal",
        "libelle": "Code postal",
        "type": "texte",
        "exemple": "57000",
        "obligatoire": False,
    },
    {
        "nom": "CT_Ville",
        "libelle": "Ville",
        "type": "texte",
        "exemple": "Metz",
        "obligatoire": False,
    },
    {
        "nom": "CT_Telephone",
        "libelle": "Téléphone",
        "type": "texte",
        "exemple": "03 87 00 00 00",
        "obligatoire": False,
    },
    {
        "nom": "CT_EMail",
        "libelle": "E-mail",
        "type": "texte",
        "exemple": "contact@fournisseur.fr",
        "obligatoire": False,
    },
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
        "champs_formulaire": CHAMPS_FORMULAIRE_TIERS,
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

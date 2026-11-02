# Étape 1 — Architecture technique proposée

Basée sur l'analyse de `01_ANALYSE_DOCUMENTATION.md`, et sur la structure
suggérée par `prompt_2.txt` (section 9), légèrement adaptée.

## Choix techniques

| Besoin | Choix | Justification |
|---|---|---|
| Langage | Python 3, **interpréteur 32 bits** | Obligatoire pour piloter l'ActiveX Sage 100 OM (32 bits). |
| Accès aux objets métiers | `pywin32` (`win32com.client.Dispatch`) | Équivalent Python de la référence COM utilisée en C#. |
| Accès SQL direct (lecture seule uniquement) | `pyodbc` vers SQL Server (`BIJOU`) | Déjà utilisé par `get_json_from_sage` ; **jamais pour écrire** (règle 8). |
| Configuration | `python-dotenv` + fichier `.env` non versionné | Évite tout mot de passe en dur dans le code (règle 8). |
| Interface de test | Menu console simple (`input()`/`print()`) | Suffisant pour un débutant, pas de dépendance UI supplémentaire. |
| Tests | `pytest` | Cohérent avec `get_json_from_sage/tests`. |

## Pourquoi un interpréteur Python 32 bits ?

L'ActiveX `Objets100c.dll` est une DLL 32 bits (voir analyse §7). Un
processus Python 64 bits ne peut pas charger une DLL COM 32 bits : il faudra
installer un Python 32 bits dédié (ex. via un second environnement virtuel
`venv32`) uniquement pour les parties qui utilisent `win32com`. La partie
lecture seule SQL (`pyodbc`) n'a pas cette contrainte et pourrait tourner en
64 bits si besoin — mais pour rester simple et éviter deux environnements,
**on démarre tout en 32 bits** et on réévaluera si cela pose un problème de
dépendance.

## Couches du projet

```
sage_Conex_CRUD/
│
├── config/
│   └── configuration.py        # Lit le .env, expose un objet Configuration
│                                #  (chemins .mae/.gcm, utilisateur, mdp,
│                                #  paramètres SQL lecture seule)
│
├── connexion/
│   ├── connexion_sage.py        # Ouvre/ferme BSCPTAApplication100c (+ .gcm
│                                 #  si présent), expose les Factory ; cf.
│                                 #  sage100_connector pour l'inspiration
│                                 #  de connexion (mais Objets Métier ici,
│                                 #  pas SQL direct)
│   └── connexion_sql.py         # Connexion pyodbc en LECTURE SEULE, pour
│                                 #  vérifier des données ou lire F_CATEGCOMPT
│                                 #  (pas d'objet métier dédié trouvé)
│
├── crud/
│   ├── gestion_crud.py           # creer(), lire(), modifier(), supprimer(),
│                                 #  lister() génériques — s'appuient sur un
│                                 #  REGISTRE_ENTITES (voir plus bas)
│   └── validations.py            # Vérifications communes : champs obligatoires,
│                                 #  clé primaire, doublons, connexion active
│
├── services/
│   ├── service_tiers.py          # Logique spécifique clients/fournisseurs
│                                 #  (distinction via CT_Type), catégories
│   ├── service_articles.py       # Logique spécifique articles/familles
│   └── service_documents.py      # creer_document() : entête + lignes + totaux
│
├── gestion_erreurs/
│   └── exceptions.py             # Exceptions Python dédiées + messages
│                                 #  [SUCCÈS]/[ERREUR]/[VALIDATION] en français
│
├── interface/
│   └── application.py            # Menu console : choisir entité + opération
│
├── tests/
│   ├── test_connexion.py
│   ├── test_crud.py
│   └── test_documents.py
│
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

Cette arborescence correspond à celle demandée dans `prompt_2.txt`, sans
modification structurelle — seul l'ajout du dossier `00_analyse/` (étape 1)
est nouveau.

## Le "registre d'entités" — comment éviter une fonction par table

`prompt_2.txt` demande explicitement de ne pas dupliquer une fonction par
table. Comme on l'a vu en §3 de l'analyse, **les Factory Sage ne sont pas
homogènes** : certaines se lisent par `ReadNumero`, d'autres par
`ReadReference`, la Famille est en version 2, etc. La bibliothèque CRUD
générique doit donc s'appuyer sur un petit **registre déclaratif** plutôt
que sur une logique identique pour toutes les entités :

```python
# Idée (pas encore codée) — crud/gestion_crud.py
REGISTRE_ENTITES = {
    "tiers": {
        "factory": lambda ctx: ctx.base_comptable.FactoryTiers,
        "lire_par_cle": "ReadNumero",
        "champ_cle": "CT_Num",
    },
    "client": {
        "factory": lambda ctx: ctx.base_comptable.FactoryClient,
        "lire_par_cle": "ReadNumero",
        "champ_cle": "CT_Num",
    },
    "article": {
        "factory": lambda ctx: ctx.base_commerciale.FactoryArticle,
        "lire_par_cle": "ReadReference",
        "champ_cle": "AR_Ref",
    },
    "famille": {
        "factory": lambda ctx: ctx.base_commerciale.FactoryFamille,  # Factory2
        "lire_par_cle": "ReadNumero",      # à confirmer à l'étape 4
        "champ_cle": "FA_CodeFamille",
    },
    # "categorie_tiers" : pas de Factory connue -> cas particulier,
    #  voir 03_QUESTIONS_OUVERTES.md
}
```

`creer()`, `lire()`, `modifier()`, `supprimer()`, `lister()` dans
`gestion_crud.py` consultent ce registre pour savoir quelle Factory
utiliser et quelle méthode appeler — une seule implémentation, pilotée par
les données du registre, pas une fonction par table. Les documents
(entête + lignes + totaux) restent à part dans `service_documents.py`
puisqu'ils ne sont pas un simple CRUD mono-objet (règle demandée en §5 de
`prompt_2.txt`).

## Gestion des erreurs et messages

Centralisée dans `gestion_erreurs/exceptions.py` :

- `ErreurConnexion`, `ErreurEntiteInconnue`, `ErreurValidation`,
  `ErreurSDKSage` (encapsule une erreur COM/pywin32 brute en message lisible).
- Chaque fonction CRUD retourne (ou lève) un résultat explicite ;
  **aucun message `[SUCCÈS]` n'est affiché avant confirmation réelle par
  Sage** (règle 6 de `prompt_2.txt`) — concrètement : on ne logue le succès
  qu'après que `WriteDefault()`/`Write()`/`Remove()` ait été appelé *sans
  exception*, et si possible après une relecture de contrôle.

## Gestion de la mémoire des objets COM

Chaque fonction de `gestion_crud.py` qui manipule un objet métier le fait
dans un bloc `try/finally` qui remet la référence Python à `None` après
usage, pour permettre au garbage collector de libérer l'objet COM
sous-jacent — en évitant de libérer un objet encore retourné à l'appelant
(ex: `lire()` renvoie l'objet converti en dictionnaire Python, pas l'objet
COM lui-même, pour ne jamais risquer de l'utiliser après libération).

## Mode lecture seule pour les premiers tests

Comme demandé en règle 8, `configuration.py` exposera un indicateur
`MODE_LECTURE_SEULE` (lu depuis `.env`). Quand il est actif,
`gestion_crud.py` refuse d'exécuter `creer()`, `modifier()`, `supprimer()`
et `creer_document()` (lève `ErreurValidation`), seules `lire()` et
`lister()` restent actives. Utile pour les étapes 2-3 avant d'être sûr du
comportement sur l'environnement réel.

## Correspondance avec les étapes de `prompt_2.txt`

| Étape | Contenu | Dossiers concernés |
|---|---|---|
| 2 | Connexion | `config/`, `connexion/` |
| 3 | CRUD générique + tiers | `crud/`, `services/service_tiers.py`, `gestion_erreurs/` |
| 4 | Articles | `services/service_articles.py` |
| 5 | Documents | `services/service_documents.py` |
| 6 | Interface | `interface/`, `main.py` |
| 7 | Tests + doc finale | `tests/`, mise à jour des README |

Chaque étape sera développée et **validée dans Sage avant de passer à la
suivante**, conformément à la méthode de travail demandée.

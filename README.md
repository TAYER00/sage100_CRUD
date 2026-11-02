# sage_Conex_CRUD

Projet Python pédagogique pour un **développeur débutant sur les Objets Métier Sage 100**.

Objectif final : une bibliothèque de fonctions CRUD (`creer`, `lire`, `modifier`,
`supprimer`, `lister`) génériques et réutilisables, qui s'appuie sur les objets
métiers Sage (COM) et leurs Factory plutôt que sur des requêtes SQL directes,
pour gérer les tiers, les articles et les documents commerciaux.

## État actuel du projet

Ce projet suit la méthode de travail demandée dans `prompt_2.txt` (à la racine
du dépôt) : **étape par étape, avec validation avant de passer à la suite.**

- [x] **Étape 1 — Analyse** : documentation étudiée, architecture proposée.
      Voir le dossier [`00_analyse/`](00_analyse/).
- [x] **Étape 2 — Connexion** (base comptable / tiers) :
      - [x] Connexion SQL en **lecture seule** à la base Sage `BIJOU`
        (`connexion/connexion_sql.py`, compte `BIJOU_READONLY`) — testée
        avec succès (`tests/test_connexion.py`, 3/3 passés).
      - [x] Connexion aux **objets métiers COM** (`connexion/
        connexion_sage.py`, ProgID réel vérifié `CPTA.Base.18` — **pas**
        `BSCPTAApplication100c` comme le suggérait le PDF, voir
        `00_analyse/04_VERIFICATION_COM.md`) — testée avec succès contre
        la vraie base Bijou SA (`tests/test_connexion_sage.py`, 3/3
        passés : 59 tiers lus, 22 clients / 25 fournisseurs).
      - [ ] Gestion Commerciale (articles/documents) : **aucune API COM
        trouvée sur ce poste** pour l'instant — voir
        `00_analyse/03_QUESTIONS_OUVERTES.md` point 6.
- [~] **Étape 3 — CRUD générique + tiers** : codé et en grande partie testé.
      - [x] `crud/registre_entites.py`, `crud/validations.py`,
        `crud/gestion_crud.py` (`creer`/`lire`/`modifier`/`supprimer`/
        `lister`) — une seule implémentation générique, pilotée par le
        registre, conformément à `docs/sage_objet_metier.docx` ("le code
        CRUD est standard et réutilisable").
      - [x] `lire()` / `lister()` testés avec succès contre les vrais
        tiers Bijou SA (`tests/test_crud.py`, 9/9 passés).
      - [x] Validations testées : identifiant/champs manquants, entité
        inconnue, mode lecture seule, suppression non supportée pour les
        tiers (aucun `Remove()` dans l'API installée).
      - [x] `creer()` / `modifier()` **testés en écriture réelle** sur un
        tiers de test (`ZZTEST01`, Bijou SA) — succès une fois `CT_Type`
        et `CG_NumPrinc` ajoutés aux champs obligatoires (voir
        `00_analyse/04_VERIFICATION_COM.md`). Ce tiers de test reste
        présent dans la base (pas de `Remove()` disponible).
      - [x] Test manuel d'écriture déplacé vers
        `tests/manuel_ecriture_reelle.py` (hors suite automatique —
        nécessite `MODE_LECTURE_SEULE=false`, à lancer explicitement).
- [ ] Étape 4 — Articles.
- [ ] Étape 5 — Documents commerciaux.
- [ ] Étape 6 — Interface de test.
- [ ] Étape 7 — Tests et documentation finale.

**Aucun code métier n'a encore été écrit.** Seuls l'analyse, l'architecture et
le squelette de dossiers (vides, avec un `README.md` expliquant leur rôle
futur) ont été créés, conformément à la consigne « Ne génère pas encore tout
le projet. Attends ma validation avant de passer à l'étape suivante. »

## À lire dans l'ordre

1. [`00_analyse/01_ANALYSE_DOCUMENTATION.md`](00_analyse/01_ANALYSE_DOCUMENTATION.md)
   — ce qui a été vérifié dans la documentation Sage (interfaces COM, cycle de
   vie, tables SQL), avec sources et numéros de page.
2. [`00_analyse/02_ARCHITECTURE_PROPOSEE.md`](00_analyse/02_ARCHITECTURE_PROPOSEE.md)
   — l'architecture technique proposée, couche par couche.
3. [`00_analyse/03_QUESTIONS_OUVERTES.md`](00_analyse/03_QUESTIONS_OUVERTES.md)
   — points qui nécessitent une décision ou une vérification de votre part
   avant de coder l'étape 2.

## Arborescence (squelette)

```
sage_Conex_CRUD/
│
├── 00_analyse/                 # Étape 1 : documents d'analyse (ce que vous lisez)
├── config/                     # Étape 2 : configuration.py, .env (non versionné)
├── connexion/                  # Étape 2 : connexion_sage.py, connexion_sql.py
├── crud/                       # Étape 3 : gestion_crud.py, validations.py
├── services/                   # Étape 3-5 : service_tiers.py, service_articles.py, service_documents.py
├── gestion_erreurs/            # Étape 3 : exceptions.py
├── interface/                  # Étape 6 : application.py (menu console en français)
├── tests/                      # Étape 7 : test_connexion.py, test_crud.py, test_documents.py
│
├── main.py                     # à créer à l'étape 6
├── requirements.txt            # dépendances (créé, voir ci-dessous)
├── .env.example                # modèle de configuration (créé, à copier en .env)
├── .gitignore                  # créé
└── README.md                   # ce fichier
```

Chaque dossier contient déjà un `README.md` qui explique son rôle avant même
que le code n'y soit écrit — utile pour un débutant qui veut comprendre la
structure avant de voir du code.

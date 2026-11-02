RUN : 
# 4. Lancer l'API + l'interface web (même serveur)
python main_api.py
Puis ouvrir :
- Interface : http://127.0.0.1:8000
- Docs API : http://127.0.0.1:8000/docs
- Santé : http://127.0.0.1:8000/sante
Sans activer le venv : .\venv32\Scripts\python.exe main_api.py









# sage_Conex_CRUD

Projet Python pédagogique pour un **développeur débutant sur les Objets Métier Sage 100**.

Objectif final : une bibliothèque de fonctions CRUD (`creer`, `lire`, `modifier`,
`supprimer`, `lister`) génériques et réutilisables, qui s'appuie sur les objets
métiers Sage (COM) et leurs Factory plutôt que sur des requêtes SQL directes,
pour gérer les tiers, les articles et les documents commerciaux.
Depuis la racine du projet (PowerShell) :
# 1. Environnement virtuel 32 bits (pywin32 / COM Sage obligatoire)
.\venv32\Scripts\Activate.ps1
# si bloqué par la policy : Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 2. Dépendances (première fois seulement)
pip install -r requirements.txt

# 3. Configuration (première fois seulement) puis renseigner les valeurs
Copy-Item .env.example .env
notepad .env



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

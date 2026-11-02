# connexion/

**À coder à l'étape 2.**

- `connexion_sage.py` : ouvre la base comptable (`BSCPTAApplication100c`,
  fichier `.mae`, obligatoire) et, si configurée, la base commerciale
  (`BSCIALApplication100c`, fichier `.gcm`), via `pywin32`. Gère
  l'authentification (`IBILoggable`), l'ouverture/fermeture propre
  (équivalent d'un context manager Python), et expose les Factory
  nécessaires aux services. S'inspire de la logique de connexion déjà
  présente dans `sage100_connector` (adaptée : ici on passe par les objets
  métiers, pas par SQL direct).
- `connexion_sql.py` : connexion **lecture seule** (`pyodbc`) à la base SQL
  Server `BIJOU`, réservée à la vérification de données et aux tables sans
  objet métier dédié (ex. `F_CATEGCOMPT`, voir
  `00_analyse/03_QUESTIONS_OUVERTES.md`). Ne doit jamais exécuter
  d'INSERT/UPDATE/DELETE.

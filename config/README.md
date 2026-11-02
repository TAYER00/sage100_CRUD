# config/

**À coder à l'étape 2.**

Contiendra `configuration.py` : lit les variables du fichier `.env` (chemins
`.mae`/`.gcm`, utilisateur/mot de passe Sage, paramètres de connexion SQL en
lecture seule, indicateur `MODE_LECTURE_SEULE`) et les expose via un objet
Python simple. Aucun mot de passe ne doit apparaître dans ce dossier
versionné — uniquement dans le `.env` local (voir `.gitignore` à la racine).

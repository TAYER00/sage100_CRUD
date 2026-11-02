# interface/

Interface web simple (HTML/CSS/JS, sans dépendance ni build) qui consomme
l'API REST/JSON du projet (voir `api/` et
`00_analyse/05_COUCHE_API.md`).

- `index.html` — page unique : connexion/entité/opération, zone de
  saisie, résultats.
- `style.css` — mise en forme simple.
- `app.js` — appels `fetch()` vers l'API (`/sante`, `/entites`,
  `/entites/{entite}`...), affichage des résultats et des messages
  `[SUCCÈS]`/`[ERREUR]`/`[VALIDATION]`.

## Lancer

Cette page est servie directement par le serveur FastAPI (pas de second
serveur à lancer, pas de souci de CORS puisque c'est la même origine) :

```
cd sage_Conex_CRUD
venv32\Scripts\python.exe main_api.py
```

Puis ouvrir http://127.0.0.1:8000/ dans un navigateur.

## Fonctionnement

1. Choisir une entité (chargée dynamiquement depuis `GET /entites`) et
   une opération (lister/lire/créer/modifier/supprimer).
2. Les champs affichés changent selon l'opération.
3. Pour créer/modifier, saisir les champs au format
   `NOM_CHAMP=valeur` (un par ligne) — voir l'exemple affiché sur la page.
4. Le résultat ou le message d'erreur/validation s'affiche, avec le code
   renvoyé par l'API.

Remplace l'interface console initialement prévue à l'étape 6 de
`prompt_2.txt` (le besoin ayant évolué vers une interface web consommant
l'API HTTP).

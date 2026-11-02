# Couche API HTTP (REST/JSON)

Expose les fonctions CRUD generiques (`crud/gestion_crud.py`) en
endpoints REST/JSON via FastAPI, avec gestion des erreurs, CORS,
pagination, et un verrou COM pour serialiser l'acces a Sage.

## Fichiers

- `api/app.py` — application FastAPI, CORS, cycle de vie, point de sante.
- `api/routes_entites.py` — endpoints REST (`/entites`, `/entites/{entite}`,
  `/entites/{entite}/{identifiant}`), pagination.
- `api/schemas.py` — corps de requete JSON (Pydantic).
- `api/gestion_erreurs_http.py` — traduction des exceptions metier en
  codes HTTP (400/404/502/503/500).
- `api/com_executor.py` — le "verrou COM" (voir plus bas, important).
- `main_api.py` — lance le serveur (`uvicorn`).

## Endpoints

| Methode | URL | Fonction CRUD | Code succes |
|---|---|---|---|
| GET | `/sante` | - (ne touche pas Sage) | 200 |
| GET | `/entites` | - (liste le registre) | 200 |
| GET | `/entites/{entite}?page=&taille_page=` | `lister()` pagine | 200 |
| GET | `/entites/{entite}/{identifiant}` | `lire()` | 200 |
| POST | `/entites/{entite}` (corps `{"donnees": {...}}`) | `creer()` | 201 |
| PUT | `/entites/{entite}/{identifiant}` (corps `{"donnees": {...}}`) | `modifier()` | 200 |
| DELETE | `/entites/{entite}/{identifiant}?confirmer=true` | `supprimer()` | 200 |

Codes d'erreur : `ErreurValidation`→400, `ErreurEntiteInconnue`→404,
`ErreurConnexion`→503, `ErreurSDKSage`→502, imprevu→500. Corps JSON
d'erreur : `{"succes": false, "type": "...", "erreur": "..."}`.

**Testes reellement contre Bijou SA** : lecture (`/entites/tiers/BAGUES`),
liste paginee (60 tiers, 12 pages de 5), entite inconnue (404), tiers
inexistant (400), creation/suppression bloquees par le mode lecture seule
(400), en-tetes CORS (`access-control-allow-origin`, preflight OPTIONS).

## Le verrou COM — decouverte importante sur ce poste

**Constat empirique (verifie par plusieurs tests independants, pas une
supposition)** : l'appel `base.Open(...)` de l'ActiveX Sage
(`CPTA.Base.18`) se bloque **tres longtemps, voire quasi indefiniment**,
des lors qu'il est invoque :

- depuis un thread secondaire (`threading.Thread` ou
  `concurrent.futures.ThreadPoolExecutor`), **meme** en amorcant une file
  de messages Windows au prealable (`win32gui.PumpWaitingMessages()`) ;
- ou simplement depuis une coroutine executee par `asyncio.run(...)`,
  **meme sur le thread principal et sans aucun thread secondaire**, avec
  `ProactorEventLoop` (defaut Windows) OU `SelectorEventLoop`.

Seul un appel **synchrone, sur le thread principal, hors de tout contexte
asyncio actif**, est rapide et fiable (quelques secondes). C'est
reproductible et independant de FastAPI : confirme par des scripts de
diagnostic autonomes (hors API), voir l'historique de la conversation pour
le detail des tests.

**Decision retenue** : ne pas utiliser de thread dedie. `api/
com_executor.py` execute les appels Sage directement sur le thread de la
boucle asyncio d'Uvicorn (le thread principal, en mode mono-processus/
mono-worker), proteges par un `asyncio.Lock()` :

```python
async def executer(fonction, *args, **kwargs):
    async with _verrou:
        connexion = _obtenir_connexion()
        return fonction(connexion, *args, **kwargs)
```

**Consequence assumee** : pendant un appel Sage, le serveur ne traite
aucune autre requete HTTP en parallele (le thread unique est occupe). Vu
sur le premier appel reel : ~1 a 2 minutes la toute premiere fois dans un
contexte asyncio (contre 2-3 secondes hors asyncio) - cause exacte non
confirmee (peut-etre lie a l'antivirus qui scanne `CptaAx.dll`/
`Maestria.exe` au premier chargement dans CE processus, ou a une
interaction specifique entre l'ActiveX et la boucle d'evenements Windows
d'asyncio) ; les appels suivants, une fois la connexion ouverte et
reutilisee, sont rapides (~1s). Ce n'est pas ideal pour une API multi-
utilisateurs a fort trafic, mais c'est coherent avec la nature de Sage
100 Objets Metiers (application de bureau, pas concue pour l'acces
concurrent) et suffisant pour ce projet pedagogique.

**Piste d'amelioration non retenue pour l'instant** : "prechauffer" la
connexion au demarrage du serveur (l'ouvrir immediatement plutot
qu'a la premiere requete) pour que le cout de la premiere ouverture ne
retombe pas sur le premier utilisateur - a reconsiderer si le delai reste
genant en pratique.

## Requêtes SQL prédéfinies, paramétrées (lecture seule)

Fichiers : `connexion/requetes_sql_predefinies.py` (registre + exécution),
`api/routes_sql.py` (`GET /requetes-sql`, `POST /requetes-sql/{nom}/executer`).

Principe : le Front-End ne connaît jamais le texte SQL. Il demande la
liste des requêtes disponibles (nom, libellé, description, et la liste de
leurs paramètres — un par `?`), génère un champ de saisie par paramètre
(avec `<datalist>`, l'équivalent HTML d'une ComboBox éditable), puis
envoie les valeurs saisies, dans l'ordre, au serveur. Le serveur les
transmet toujours à pyodbc comme paramètres positionnels (`?`) — jamais
insérées dans le texte SQL. **Testé avec une tentative d'injection SQL
réelle** (`BAGUES'; DROP TABLE F_CONTACTT; --`) : traitée comme une simple
valeur de recherche (0 résultat), aucune exécution de la commande
injectée.

Pour ajouter une nouvelle requête : ajouter une entrée dans
`REGISTRE_REQUETES` (libellé, SQL avec ses `?`, liste des paramètres dans
le même ordre) — aucune autre modification nécessaire, le Front-End et
l'API s'adaptent automatiquement.

Deux requêtes fournies en exemple, vérifiées contre `F_CONTACTT` et
`F_COMPTET` réels : `contacts_par_tiers` (reprend l'exemple fourni) et
`tiers_par_ville`.

## Lancer l'API

```
cd sage_Conex_CRUD
venv32\Scripts\python.exe main_api.py
```

Documentation interactive : http://127.0.0.1:8000/docs

# Étape 1 — Points à valider avant l'étape 2

Ces points ne peuvent pas être tranchés depuis la documentation seule : ils
dépendent de votre poste de travail ou d'un choix de votre part.

## 1. Environnement Python 32 bits — ✅ résolu

Les 4 interpréteurs Python déjà installés (3.10, 3.11, 3.12, 3.13) étaient
tous en 64 bits. `winget` refusant d'installer une variante x86 d'un ID déjà
présent en 64 bits, un **Python 3.11.9 32 bits a été installé directement
depuis python.org** dans `C:\Python311-32\` (installation isolée,
`PrependPath=0` : n'affecte pas le PATH ni les Python existants).

Un environnement virtuel dédié a été créé dans le projet :
`sage_Conex_CRUD/venv32/` (via `C:\Python311-32\python.exe -m venv venv32`).
Les dépendances de `requirements.txt` (`pywin32`, `python-dotenv`, `pyodbc`,
`pytest`) y sont installées et s'importent correctement — confirmé par :

```
venv32\Scripts\python.exe -c "import win32com.client; import dotenv; import pyodbc; import pytest"
```

`venv32/` est ignoré par `.gitignore` (ne pas le committer).

**Résolu** — voir `00_analyse/04_VERIFICATION_COM.md` pour le détail complet.
Le ProgID réel, vérifié par inspection directe de la bibliothèque de types
COM et confirmé par un test de connexion réel contre Bijou SA, est
**`CPTA.Base.18`** (pas `BSCPTAApplication100c`, qui n'existe pas sur ce
poste — le PDF documente une autre famille d'API). `connexion/
connexion_sage.py` est écrit et testé (3/3 tests passés,
`tests/test_connexion_sage.py`) : ouverture, lecture de 59 tiers réels
(22 clients, 25 fournisseurs), fermeture.

**Nouveau point ouvert** : aucune API COM trouvée pour la Gestion
Commerciale (articles/familles/documents) sur ce poste — `GecoMaes.exe` ne
s'enregistre pas comme bibliothèque de types. Voir §6 ci-dessous.

**Autre point à trancher pour l'étape 3** : aucune méthode `Remove()`
trouvée pour les tiers dans l'API COM réelle (ni sur l'objet ni sur sa
collection, dans aucune version). La suppression de tiers via objets
métiers n'est peut-être simplement pas supportée par Sage (cohérent avec
les contraintes comptables) — à confirmer avant de coder `supprimer()`
pour les tiers.

## 6. Gestion Commerciale (articles, documents) non accessible via COM sur ce poste

Contrairement à la Comptabilité (tiers), aucune bibliothèque de types n'est
enregistrée pour la Gestion Commerciale : `GecoMaes.exe` ne s'ouvre pas
comme bibliothèque de types COM, et aucun fichier équivalent à `CptaAx.dll`
n'existe pour la gestion commerciale dans `Common Files\Sage`.

**Question** : voulez-vous que je lance `GecoMaes.exe` manuellement (vous,
pas moi automatiquement — c'est une application graphique) pour voir si
cela déclenche un auto-enregistrement COM au premier lancement ? Ou
préférez-vous vérifier dans l'installeur Sage 100c si un composant
"Objets Métiers"/SDK développeur optionnel est manquant ? Sans cela, les
articles et documents (étapes 4 et 5) ne pourront pas utiliser les objets
métiers et devront, au moins temporairement, passer par la lecture SQL
seule — ce qui va à l'encontre de la préférence du cahier des charges pour
les objets métiers.

## 2. Accès à Sage 100c et aux fichiers `.mae` / `.gcm` — ✅ confirmé

Sage 100 Entreprise est installé dans
`C:\Program Files (x86)\Sage\Entreprise 100c\` (le `(x86)` confirme le
32 bits). Les raccourcis du menu Démarrer pointent vers la société **Bijou
SA**, avec les fichiers suivants (vérifiés présents sur le disque) :

- Base comptable : `C:\Users\Public\Documents\Sage\Entreprise 100c\BIJOU.MAE`
- Base commerciale : `C:\Users\Public\Documents\Sage\Entreprise 100c\Bijou.gcm`

Ces deux chemins seront utilisés dans le `.env` de l'étape 2
(`SAGE_CHEMIN_BASE_COMPTABLE`, `SAGE_CHEMIN_BASE_COMMERCIALE`). Il reste à
obtenir un identifiant/mot de passe Sage valide pour l'authentification
(`IBILoggable`) — à fournir au moment de coder la connexion, pas à mettre
dans ce dépôt.

## 3. Catégories de tiers (`F_CATEGCOMPT`)

Aucun objet métier dédié n'a été trouvé dans le PDF OM pour les catégories de
tiers (section 5.A de `prompt_2.txt`). Deux options :

- **Option A (proposée)** : les lister en **lecture seule** via
  `connexion_sql.py` (SELECT uniquement sur `F_CATEGCOMPT`), sans jamais les
  écrire — cohérent avec la règle « ne jamais modifier directement les
  tables Sage », puisqu'on ne fait que lire.
- **Option B** : vérifier directement dans l'explorateur de types COM
  (OLE/COM Viewer) installé avec Sage 100c s'il existe une interface
  `IBOCategorieTiers*` non documentée dans ce PDF, avant de conclure à son
  absence.

**Question** : qui fait la vérification de l'option B (poste avec Sage
installé), ou validez-vous directement l'option A ?

## 4. Codes des types de documents

Les valeurs du tableau §5 de l'analyse (Devis=0, BonCommande=1, etc.) sont
documentées dans le PDF mais pas revérifiées contre l'énumération réellement
exposée par la version de SDK installée. À l'étape 5, il faudra les
confirmer (par exemple en inspectant l'énumération `DocumentType*` via
`win32com.client` sur le poste cible) avant de les coder en dur.

## 5. Choix définitif `Create()+WriteDefault()` vs `Create()+Write()`

La documentation recommande `WriteDefault()` à la création (règle suivie par
défaut dans ce projet, et explicitement attendue par `prompt_2.txt` §4).
Le projet C# existant utilise `Write()` et semble fonctionner. À tester
concrètement à l'étape 3 sur un tiers de test, pour confirmer que
`WriteDefault()` fonctionne bien dans cet environnement précis (versions de
Sage 100c pouvant légèrement varier).

---

**Prochaine étape proposée (Étape 2 — Connexion)** dès que les points 1 et 2
sont clarifiés : écrire `config/configuration.py` et
`connexion/connexion_sage.py`, puis un test manuel d'ouverture/fermeture de
session sur la société réelle.

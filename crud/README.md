# crud/

**À coder à l'étape 3.**

- `gestion_crud.py` : les 5 fonctions génériques demandées par
  `prompt_2.txt` — `creer()`, `lire()`, `modifier()`, `supprimer()`,
  `lister()` — pilotées par un petit registre déclaratif d'entités (voir
  `00_analyse/02_ARCHITECTURE_PROPOSEE.md`, section « registre
  d'entités ») plutôt que par une implémentation dédiée par table.
- `validations.py` : vérifications communes à toutes les entités (champ
  clé obligatoire, connexion active, existence avant modification/
  suppression, détection de doublon avant création).

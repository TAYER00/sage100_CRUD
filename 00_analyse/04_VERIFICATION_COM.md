# Étape 2 — Vérification réelle de l'API COM sur ce poste

**Ce document prime sur `01_ANALYSE_DOCUMENTATION.md` pour tout ce qui
concerne les objets métiers COM** : il documente ce qui a été vérifié par
inspection directe du registre Windows et de la bibliothèque de types COM
installée sur ce poste, puis confirmé par une connexion réelle à la base
comptable **Bijou SA**. Conformément à la règle 13 de `prompt_2.txt`
(« ne pas inventer de méthodes ou de propriétés, vérifier les noms exacts »),
ces faits vérifiés remplacent les noms déduits du PDF `V12_Sage 100cloud
Objets metiers v1220.pdf` dès qu'il y a conflit.

## Résultat principal : l'API installée n'est pas celle du PDF

Le PDF décrit une famille d'interfaces `IBOTiers3` / `IBOClient3` /
`BSCPTAApplication100c`. **Aucune de ces interfaces n'est enregistrée sur ce
poste.** Recherche effectuée : scan complet du registre
(`HKEY_CLASSES_ROOT\CLSID`, `HKLM\SOFTWARE\WOW6432Node\Classes\CLSID`,
`...\TypeLib`) pour tout CLSID ou bibliothèque de types dont le nom ou le
chemin contient "Sage", "100c", "Objet", "BSCPTA", "BSCIAL" → zéro
correspondance avec les noms du PDF.

En revanche, une bibliothèque de types **est bien enregistrée** et
fonctionne réellement :

| Élément | Valeur vérifiée |
|---|---|
| Nom de la bibliothèque | `CPTAAx Sage 18.0 Type Library` |
| Fichier | `C:\Program Files (x86)\Common Files\Sage\CptaAx.dll` |
| Classe de base (comptabilité) | coclasse `CPTABase18` |
| **ProgID à utiliser** | **`CPTA.Base.18`** |

C'est la famille historique **"CPTA"** (héritée des anciennes gammes Sage
Ciel/Compta), pas la famille "Objets Métiers IBO*" documentée dans le PDF
fourni. Le PDF décrit donc une version/édition différente de celle
installée sur ce poste (ou un module non installé ici) : **on code contre
l'API réellement présente**, pas contre le PDF.

## Méthode de vérification

1. Script Python utilisant `pythoncom.LoadTypeLib()` / `LoadRegTypeLib()`
   pour énumérer directement les coclasses, interfaces, méthodes et
   propriétés de `CptaAx.dll` et de `Maestria.exe` (qui héberge une
   bibliothèque de types `CPTAAppl` distincte, pour `CPTAApplication3`,
   non utilisée finalement - voir plus bas).
2. Résolution des ProgID via le registre
   (`HKEY_CLASSES_ROOT\CLSID\{guid}\ProgID`).
3. **Test de connexion réel** contre
   `C:\Users\Public\Documents\Sage\Entreprise 100c\BIJOU.MAE` : ouverture,
   lecture de tiers existants, fermeture — exécuté avec succès (voir
   `tests/test_connexion_sage.py`, 3/3 passés).

## API vérifiée pour les Tiers (clients/fournisseurs)

```python
import win32com.client

base = win32com.client.gencache.EnsureDispatch("CPTA.Base.18")
base.Open(r"C:\Users\Public\Documents\Sage\Entreprise 100c\BIJOU.MAE")

tiers = base.CompteTs               # collection (Factory) des tiers
tiers.Count                         # nombre total de tiers
un_tiers = tiers.Item(1)            # acces par INDICE (1-based), pas par cle
un_tiers.CT_Num, un_tiers.CT_Intitule, un_tiers.CT_Type

client = base.ReadCompteTNumero("BAGUES")   # lecture par CLE (CT_Num)
client.CT_Num, client.CT_Intitule

clients = base.QueryCompteTTypeOrderNumero(0)       # CT_Type=0 -> clients
fournisseurs = base.QueryCompteTTypeOrderNumero(1)  # CT_Type=1 -> fournisseurs

base.Close()
```

Résultat du test réel sur Bijou SA : **59 tiers** au total, **22 clients**
(`CT_Type=0`) et **25 fournisseurs** (`CT_Type=1`) - cohérent avec le
mapping `CT_Type` documenté dans `01_ANALYSE_DOCUMENTATION.md` (0=Client,
1=Fournisseur, 2=Salarié, 3=Autre), lui-même confirmé par la structure SQL
réelle de `F_COMPTET`.

Champs disponibles sur un objet tiers (`ICPTACompteT8`, interface la plus
récente trouvée) : `CT_Num`, `CT_Intitule`, `CT_Type`, `CG_NumPrinc`,
`CT_Contact`, `CT_Adresse`, `CT_Complement`, `CT_CodePostal`, `CT_Ville`,
`CT_Pays`, `CT_Identifiant`, `CT_Telephone`, `CT_Telecopie`, `CT_EMail`,
`CT_Site`, `CT_Classement`, `CT_Qualite`, `CT_Ape`, `CT_Siret`,
`CT_Sommeil`, `CT_Saut`, `CT_DateCreate`, `CT_InfoLibre(nom)`, plus les
collections `BanqueTs`/`ReglementTs` et une méthode `Write()`.

Cycle de vie vérifié pour les tiers :

| Opération demandée | Méthode COM vérifiée |
|---|---|
| CREATE | `base.CompteTs.AddNew()` puis renseigner les champs puis `.Write()` *(AddNew/Write confirmés présents dans la bibliothèque de types ; pas encore testés en écriture - voir note sécurité ci-dessous)* |
| READ | `base.ReadCompteTNumero(CT_Num)` |
| UPDATE | `ReadCompteTNumero(...)` puis modifier les champs puis `.Write()` |
| DELETE | **Aucune méthode `Remove()` trouvée**, ni sur l'objet tiers ni sur sa collection, dans aucune des 8 versions d'interface (`ICPTACompteT` à `T8`, `ICPTACompteTs` à `Ts8`). Cohérent avec une contrainte comptable Sage (un tiers ayant des écritures ne doit pas être supprimable par API) - **à confirmer explicitement avant de coder `supprimer()` pour les tiers** : il faudra soit accepter que cette opération n'est pas supportée pour les tiers, soit chercher une méthode alternative (ex: "mise en sommeil" via `CT_Sommeil`, un champ déjà repéré). |

### Écriture réelle testée (étape 3) : CT_Type et CG_NumPrinc sont obligatoires

Un premier test d'écriture réelle (`CompteTs.AddNew()` avec seulement
`CT_Num`/`CT_Intitule`) a **échoué** avec l'erreur Sage :

```
(-2147352567, 'Une exception s'est produite.',
 (0, None, "Problème à l'écriture d'un enregistrement dans le fichier
 comptes de tiers !", None, 0, -9016), None)
```

Cause identifiée en consultant `V12_Sage 100cloud Objets metiers v1220.pdf` :
la documentation officielle (page 75-76) crée un tiers via une **Factory
différente par type** (`FactoryClient`/`FactoryFournisseur`/
`FactoryTiersSalarie`/`FactoryTiersAutre`) puis `SetDefault()` avant
`WriteDefault()` - `SetDefault()` dérive alors automatiquement le compte
général lié (`CompteGPrinc`) à partir du type choisi. L'API réellement
installée ici (`CPTA.Base.18`) n'a ni Factory par type, ni `SetDefault()` :
il faut donc renseigner **manuellement** `CT_Type` et `CG_NumPrinc` avant
`Write()`.

**Deuxième test, avec ces deux champs ajoutés : succès confirmé.**
Tiers de test réel créé puis modifié dans Bijou SA (60e tiers) :

```python
creer(connexion, "tiers", {
    "CT_Num": "ZZTEST01",
    "CT_Intitule": "TIERS DE TEST CRUD - A IGNORER",
    "CT_Type": 0,            # 0=Client (voir mapping F_COMPTET)
    "CG_NumPrinc": "4110000",  # compte general "clients" existant,
                                # reutilise d'autres tiers CT_Type=0 reels
                                # (BAGUES, CARAT, CERAM...)
})
```

`crud/registre_entites.py` a été mis à jour : `champs_obligatoires` pour
"tiers" inclut maintenant `CT_Num`, `CT_Intitule`, `CT_Type`,
`CG_NumPrinc`. `CG_NumPrinc` doit référencer un compte général **existant**
(table `F_COMPTEG`) - pas une valeur inventée ; en pratique, un service
métier (étape 3 avancée) devrait proposer un compte général par défaut
selon le type de tiers plutôt que de l'exiger de l'appelant à chaque fois.

Bug corrigé au passage : `valider_champs_obligatoires()` traitait
`CT_Type=0` comme "manquant" (0 est une valeur légitime, pas une valeur
vide) - corrigé pour ne considérer comme manquant qu'une clé absente,
`None`, ou une chaîne vide.

## Piège technique important : liaison dynamique vs anticipée

`win32com.client.Dispatch("CPTA.Base.18")` (liaison dynamique classique)
**échoue** à l'exécution dès qu'on accède à une propriété de collection
comme `CompteTs` : erreur COM `(-2147352573, 'Membre introuvable.')`.

Seul `win32com.client.gencache.EnsureDispatch("CPTA.Base.18")` (liaison
anticipée : génère un wrapper Python depuis la bibliothèque de types)
fonctionne - confirmé par test réel. `connexion/connexion_sage.py` utilise
donc systématiquement `gencache.EnsureDispatch`, jamais `Dispatch` seul.

Autre piège constaté : le plugin `faulthandler` de `pytest` provoque un
**crash natif Windows** (code `0xc06d007e`) lors d'un appel COM
(`EnsureDispatch`) exécuté depuis un test pytest - sans rapport avec le
code du projet. Corrigé une fois pour toutes via `pytest.ini`
(`addopts = -p no:faulthandler`) à la racine du projet.

## Partie Gestion Commerciale (articles, familles, documents) — NON disponible sur ce poste

Aucune bibliothèque de types n'est enregistrée pour la Gestion
Commerciale sur ce poste : `GecoMaes.exe` (l'exécutable de Gestion
Commerciale) ne s'ouvre pas comme bibliothèque de types
(`pythoncom.LoadTypeLib` échoue), et `C:\Program Files (x86)\Common
Files\Sage\` ne contient aucun fichier équivalent à `CptaAx.dll` pour la
gestion commerciale (pas de `GcAx.dll` ou analogue).

**Conséquence** : à ce stade, impossible de confirmer une API COM pour les
articles/familles/documents sur ce poste. Options possibles (voir
`03_QUESTIONS_OUVERTES.md`, mis à jour) :

1. Lancer `GecoMaes.exe` au moins une fois (certains composants Sage
   s'auto-enregistrent au premier lancement de l'application graphique) -
   **je ne l'ai pas fait automatiquement** : c'est une application
   graphique, à lancer et fermer manuellement.
2. Vérifier dans l'installeur Sage 100c si un composant "Objets Métiers"
   / "SDK développeur" optionnel existe et n'a pas été installé.
3. Si la Gestion Commerciale COM reste indisponible, les articles et
   documents devront être traités en lecture seule via SQL
   (`connexion_sql.py`) en attendant, ce qui contredirait la préférence
   pour les objets métiers - à rediscuter avec vous le cas échéant.

## Ce qui n'a pas changé

Le reste de l'analyse (`01_ANALYSE_DOCUMENTATION.md`) reste valable :
moteur SQL (SQL Server, `BIJOU`), structure des tables `F_COMPTET` /
`F_ARTICLE` / `F_FAMILLE` / `F_DOCENTETE` / `F_DOCLIGNE`, et le mapping
`CT_Type` (qui vient d'être confirmé une seconde fois par les comptages
réels 22 clients / 25 fournisseurs).

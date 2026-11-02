# Étape 1 — Analyse de la documentation Sage 100

Sources consultées :

- `docs/V12_Sage 100cloud Objets metiers v1220.pdf` (489 pages) — SDK Objets Métier (OM).
- `docs/V12_Sage 100_Structure des fichiers v1225.pdf` (450 pages) — structure des tables SQL.
- `docs/sage_objet_metier.docx` — notes de synthèse.
- `docs/MCP_SQLSERVER_BIJOU.md` + schéma réel de la base **BIJOU** (via le serveur MCP `bijou-readonly`, lecture seule).
- `SageOM.LearningProject/` — projet C# déjà réalisé à partir des mêmes PDF (réutilisé pour vérifier les noms exacts).
- `get_json_from_sage/` — projet Python existant qui lit déjà BIJOU en SQL direct (conventions de connexion, `.env`).

Convention utilisée ci-dessous : **VÉRIFIÉ** (trouvé explicitement dans une
source citée), **DÉDUIT** (raisonnable mais pas lu noir sur blanc), **NON
TROUVÉ** (à vérifier à l'exécution, ne pas supposer).

## 1. Moteur de base de données

**VÉRIFIÉ** — SQL Server, base `BIJOU`. Confirmé par connexion réelle en
lecture seule (`bijou-readonly`, rôle `db_datareader`) et par
`get_json_from_sage` qui s'y connecte déjà en direct (compte `sa`, via
`pyodbc`). Pas de PostgreSQL dans cet environnement.

## 2. Point d'accès : pas de « moteur » central

**VÉRIFIÉ** (README `SageOM.LearningProject`, doc OM p.21) — Sage 100 OM n'a
pas d'objet "Engine" séparé. Le point d'entrée est l'instanciation directe
d'une classe COM représentant une base :

- `BSCPTAApplication100c` → base **comptable** (fichier `.mae`), **toujours
  nécessaire**, porte les tiers (`FactoryClient`, `FactoryFournisseur`,
  `FactoryTiers`).
- `BSCIALApplication100c` → base **commerciale** (fichier `.gcm`),
  **facultative**, référence obligatoirement sa base comptable via sa
  propriété `CptaApplication`. Porte les articles et les documents
  (`FactoryArticle`, `FactoryFamille`, `FactoryDocumentVente`).
- Authentification : caster l'objet en `IBILoggable` et renseigner
  `UserName` / `UserPwd` avant `.Open()`.

Conséquence pour la gestion des documents (vente **et** achat) : la base
commerciale doit être ouverte, et il faudra vérifier si une Factory distincte
existe pour les documents d'achat ou si `FactoryDocumentVente`/
`IBODocumentFactory` gère les deux domaines via le champ `DO_Domaine`
(voir §5).

## 3. Interfaces et Factory vérifiées

| Entité | Interface objet | Factory | Méthode de lecture par clé |
|---|---|---|---|
| Tiers (base) | `IBOTiers3` | `IBOTiersFactory3` | `ReadNumero` |
| Client | `IBOClient3` | `IBOClientFactory3` (`BaseComptable.FactoryClient`) | `ReadNumero`, `ExistNumero` |
| Fournisseur | *(spécialisation tiers, p.3260-3268)* | `IBOFournisseurFactory3` | `ReadNumero` |
| Article | `IBOArticle3` | `IBOArticleFactory3` (`BaseCommerciale.FactoryArticle`) | `ReadReference`, `ExistReference` |
| Famille d'articles | `IBOFamille3` | `IBOFamilleFactory2` ⚠️ (suffixe différent, réel) | — |
| Document de vente | `IBODocumentVente3` | `FactoryDocumentVente` / `IBODocumentFactory` générique | — |
| Ligne de document | `IBODocumentLigne3` | — (créée depuis le document entête) | — |
| Interfaces transverses | `IBIPersistObject`, `IBILoggable`, `IBIPersistStream`, `IBICollection` | — | — |

**NON TROUVÉ** — aucun objet métier dédié pour `F_CATEGCOMPT` (catégories de
tiers) dans les 489 pages du PDF OM. Point à traiter en étape ouverte
(voir `03_QUESTIONS_OUVERTES.md`).

⚠️ Remarque importante : le suffixe de version n'est **pas uniforme**
(`*Factory3` pour Client/Article/Tiers, mais `*Factory2` pour Famille). Ce
n'est pas une coquille à corriger — c'est documenté ainsi et doit être
respecté tel quel dans le code.

## 4. Cycle de vie des objets (Create / Read / Write / WriteDefault / Remove)

**VÉRIFIÉ** (doc OM p.61-62) :

| Étape | Méthode | Effet |
|---|---|---|
| 1 | `Factory.Create()` | Crée l'objet **en mémoire uniquement**, pas encore en base. |
| 2 | `objet.SetDefault()` | Remplit uniquement les champs encore vides avec les valeurs par défaut Sage. |
| 3 | renseigner les champs métier (ex. `CT_Num`, `CT_Intitule`...) | — |
| 4 | `objet.WriteDefault()` | **Première écriture réelle** après une création. Déclenche aussi des effets métier (ex. reprise des tarifs de la famille pour un article, création automatique d'une adresse de livraison pour un client). |
| — | `objet.Write()` | Écriture d'une **mise à jour** sur un objet déjà persistant (pas une création). |
| — | `Factory.ReadNumero(cle)` / `ReadReference(cle)` | Charge un objet existant depuis la base. |
| — | `objet.Remove()` | Supprime l'enregistrement. |

Règle de correspondance avec les opérations CRUD demandées :

- **CREATE** = `Create()` → `SetDefault()` → renseigner les champs → `WriteDefault()`.
- **READ** = `Factory.ReadNumero(...)` / `ReadReference(...)`.
- **UPDATE** = `Read(...)` puis renseigner les champs puis `Write()`.
- **DELETE** = `Read(...)` puis `Remove()`.

⚠️ **Incohérence relevée** : le projet C# `SageOM.LearningProject` (déjà
écrit) utilise `Create()` → `SetDefault()` → `Write()` (pas `WriteDefault()`)
pour créer un client, et ça fonctionne apparemment. Le PDF documente bien
`WriteDefault()` comme l'écriture dédiée à la création, avec des effets de
bord spécifiques. **Pour ce projet Python, on suivra la documentation
(`WriteDefault()` à la création) comme demandé par `prompt_2.txt`**, mais ce
point devra être vérifié concrètement à l'étape 3 (tester les deux si
`WriteDefault()` lève une erreur sur une entité donnée).

## 5. Codes des types de documents

**VÉRIFIÉ** (structure des fichiers p.246, confirmé par les noms d'énumération
du SDK OM) :

| Domaine (`DO_Domaine`) | Type (`DO_Type`) | Document |
|---|---|---|
| 0 = Vente | 0 | Devis (`DocumentTypeVenteDevis`) |
| 0 = Vente | 1 | Bon de commande client (`DocumentTypeVenteCommande`) |
| 0 = Vente | 3 | Bon de livraison (`DocumentTypeVenteLivraison`) |
| 0 = Vente | 6 (7 = comptabilisée) | Facture de vente (`DocumentTypeVenteFacture`) |
| 1 = Achat | 12 | Bon de commande fournisseur (`DocumentTypeAchatCommande`) |
| 1 = Achat | 16 (17 = comptabilisée) | Facture d'achat (`DocumentTypeAchatFacture`) |

Ces valeurs sont documentées mais **doivent être revérifiées au moment de
coder l'étape 5**, directement contre l'énumération exposée par le SDK
installé sur le poste (nom exact de l'énumération .NET/COM, pas seulement la
valeur numérique), conformément à la règle « ne pas inventer de
méthodes/propriétés » de `prompt_2.txt`.

## 6. Tables SQL (lecture seule, pour vérification — pas pour écrire)

**VÉRIFIÉ** (PDF structure des fichiers + schéma réel BIJOU) :

- **`F_COMPTET`** (tiers) — clé primaire `CT_Num` (varchar 17, majuscules).
  `CT_Intitule` (varchar 69) = nom. **`CT_Type`** (smallint) distingue la
  nature : `0=Client`, `1=Fournisseur`, `2=Salarié`, `3=Autre`.
- **`F_ARTICLE`** — clé primaire `AR_Ref` (18), `AR_Design` (69) = libellé,
  `FA_CodeFamille` → FK vers `F_FAMILLE`.
- **`F_FAMILLE`** — clé primaire `FA_CodeFamille` (10), `FA_Type` (0/1/2).
- **`F_DOCENTETE`** / **`F_DOCLIGNE`** — clé composite `DO_Domaine` +
  `DO_Type` + `DO_Piece` (13) commune aux deux tables ; les lignes ajoutent
  `DL_Ligne`. FK `CT_Num` → `F_COMPTET` (tiers du document), FK `AR_Ref` →
  `F_ARTICLE` sur les lignes.
- **`F_CATEGCOMPT`** — **NON TROUVÉ** dans cette édition du PDF structure des
  fichiers (absente du document fourni).

Ces tables **ne doivent jamais être écrites directement** (règle 8 de
`prompt_2.txt`) : elles ne servent ici qu'à vérifier/lire en lecture seule
(via le compte `bijou-readonly` existant) pour valider que les objets métiers
Sage produisent bien les enregistrements attendus, pas à les modifier.

## 7. Prérequis COM / Python

**VÉRIFIÉ** (README `SageOM.LearningProject`, `objet_metier.txt`) — l'ActiveX
Objets Métier Sage 100 (`Objets100c.dll`) est une **librairie 32 bits**. Toute
application qui le pilote doit tourner en 32 bits. Pour le C#, cela veut dire
compiler en x86 ; **pour Python, cela veut dire utiliser un interpréteur
Python 32 bits** (pas le 64 bits habituel) avec le module `pywin32`
(`win32com.client.Dispatch`), qui joue le même rôle que la référence COM
Visual Studio.

Autres prérequis :

- Sage 100c doit être installé sur le poste qui exécute le script (c'est lui
  qui enregistre l'ActiveX).
- Les fichiers `.mae` (base comptable, obligatoire) et `.gcm` (base
  commerciale, facultative) doivent être accessibles en lecture/écriture par
  l'utilisateur Windows qui lance le script.

## 8. Synthèse des incohérences relevées

1. Factory de Famille en version `2` alors que les autres entités sont en
   version `3` — à respecter tel quel, pas une erreur.
2. `Create()+Write()` vs `Create()+WriteDefault()` pour la création — le
   projet C# utilise la première forme, la documentation la seconde ; on
   suivra la documentation et on vérifiera à l'usage (étape 3).
3. Aucun objet métier dédié trouvé pour les catégories de tiers
   (`F_CATEGCOMPT`) — voir question ouverte.
4. Les codes de types de documents sont documentés mais pas revérifiés
   contre le SDK réellement installé — à faire avant de coder l'étape 5.

# services/

**À coder progressivement aux étapes 3, 4 et 5.**

- `service_tiers.py` (étape 3) : clients et fournisseurs (table partagée
  `F_COMPTET`, distingués par `CT_Type`), catégories de tiers.
- `service_articles.py` (étape 4) : articles et familles d'articles.
- `service_documents.py` (étape 5) : documents commerciaux complets
  (devis, commande client, livraison, facture de vente, commande
  fournisseur, facture d'achat) — gère l'entête, l'ajout des lignes, les
  relations tiers/articles et le calcul des totaux selon les règles
  métier Sage. Ce n'est pas un simple CRUD mono-table : une fonction
  dédiée `creer_document()` orchestre la création complète.

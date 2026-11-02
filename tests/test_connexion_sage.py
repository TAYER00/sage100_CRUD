"""
Tests de la connexion aux objets metiers Sage 100 (COM, base comptable).

Lecture seule uniquement (ouverture, lecture de tiers existants, fermeture)
- aucune ecriture n'est testee ici. Necessite que Sage 100 Entreprise soit
installe sur ce poste (ProgID "CPTA.Base.18" enregistre) et que le chemin
SAGE_CHEMIN_BASE_COMPTABLE du .env soit valide.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from connexion.connexion_sage import ConnexionSage


def test_ouverture_et_fermeture():
    """La base comptable doit pouvoir s'ouvrir puis se fermer sans erreur."""
    connexion = ConnexionSage()
    connexion.ouvrir()
    assert connexion.est_ouverte is True
    connexion.fermer()
    assert connexion.est_ouverte is False


def test_lecture_tiers_existants():
    """CompteTs doit contenir des tiers, lisibles individuellement."""
    with ConnexionSage() as connexion:
        tiers = connexion.base_comptable.CompteTs
        assert tiers.Count > 0

        premier = tiers.Item(1)
        assert premier.CT_Num

        relu = connexion.base_comptable.ReadCompteTNumero(premier.CT_Num)
        assert relu.CT_Num == premier.CT_Num
        assert relu.CT_Intitule == premier.CT_Intitule


def test_filtre_par_type_client_fournisseur():
    """QueryCompteTTypeOrderNumero doit filtrer correctement par CT_Type."""
    with ConnexionSage() as connexion:
        clients = connexion.base_comptable.QueryCompteTTypeOrderNumero(0)
        fournisseurs = connexion.base_comptable.QueryCompteTTypeOrderNumero(1)
        assert clients.Count > 0
        assert fournisseurs.Count > 0

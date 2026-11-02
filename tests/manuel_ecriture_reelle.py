"""
Test MANUEL d'ecriture reelle sur Bijou SA - NE PAS inclure dans la suite
automatisee habituelle (nom volontairement hors du motif test_*.py standard
de pytest... en realite ce fichier suit le motif pour pouvoir etre lance
explicitement, mais il cree une donnee REELLE et PERMANENTE (voir
00_analyse/04_VERIFICATION_COM.md : aucun Remove() pour les tiers) :

    venv32\\Scripts\\python.exe -m pytest tests/test_ecriture_reelle_manuel.py -v

Necessite MODE_LECTURE_SEULE=false dans .env. Cree un tiers de test
clairement identifiable (CT_Num="ZZTEST01") puis le modifie. Ne le lance
PAS a chaque execution normale de la suite de tests.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from connexion.connexion_sage import ConnexionSage
from crud.gestion_crud import creer, lire, modifier
from gestion_erreurs.exceptions import ErreurValidation

CODE_TEST = "ZZTEST01"


@pytest.fixture
def connexion():
    with ConnexionSage() as cnx:
        yield cnx


def test_01_creer_tiers_de_test_reel(connexion):
    """creer() doit ecrire reellement un nouveau tiers dans Bijou SA."""
    deja_present = False
    try:
        lire(connexion, "tiers", CODE_TEST)
        deja_present = True
    except ErreurValidation:
        pass

    if deja_present:
        pytest.skip(f"{CODE_TEST} existe deja (test deja joue precedemment).")

    resultat = creer(
        connexion,
        "tiers",
        {
            "CT_Num": CODE_TEST,
            "CT_Intitule": "TIERS DE TEST CRUD - A IGNORER",
            # CT_Type et CG_NumPrinc renseignes manuellement : l'API COM
            # reellement installee (CPTA.Base.18) n'a pas de SetDefault()
            # ni de Factory par type pour les deriver automatiquement
            # (contrairement a l'API documentee dans le PDF OM, voir
            # 00_analyse/04_VERIFICATION_COM.md). CG_NumPrinc="4110000"
            # est le compte general "clients" reellement utilise par
            # d'autres tiers CT_Type=0 existants (BAGUES, CARAT, CERAM...).
            "CT_Type": 0,
            "CG_NumPrinc": "4110000",
        },
    )
    assert resultat["succes"] is True
    assert resultat["cle"] == CODE_TEST

    relecture = lire(connexion, "tiers", CODE_TEST)
    assert relecture["donnees"]["CT_Intitule"] == "TIERS DE TEST CRUD - A IGNORER"


def test_02_modifier_tiers_de_test_reel(connexion):
    """modifier() doit ecrire reellement une mise a jour sur ce tiers."""
    resultat = modifier(
        connexion,
        "tiers",
        CODE_TEST,
        {"CT_Intitule": "TIERS DE TEST CRUD - MODIFIE"},
    )
    assert resultat["succes"] is True

    relecture = lire(connexion, "tiers", CODE_TEST)
    assert relecture["donnees"]["CT_Intitule"] == "TIERS DE TEST CRUD - MODIFIE"


def test_03_creer_un_doublon_echoue(connexion):
    """creer() doit refuser de recreer un tiers avec la meme cle (doublon)."""
    with pytest.raises(ErreurValidation):
        creer(
            connexion,
            "tiers",
            {"CT_Num": CODE_TEST, "CT_Intitule": "Doublon"},
        )

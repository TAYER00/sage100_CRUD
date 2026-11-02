"""
Tests des fonctions CRUD generiques (crud/gestion_crud.py) sur l'entite
"tiers", contre la vraie base Bijou SA.

Lecture seule uniquement : lire()/lister() sont testes contre des donnees
reelles. creer()/modifier()/supprimer() sont testes UNIQUEMENT pour
verifier qu'ils refusent correctement d'ecrire (mode lecture seule actif
par defaut dans .env, et suppression non supportee pour les tiers) -
aucune ecriture reelle n'est effectuee ici.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from connexion.connexion_sage import ConnexionSage
from crud.gestion_crud import creer, lire, lister, modifier
from crud.registre_entites import REGISTRE_ENTITES
from gestion_erreurs.exceptions import ErreurEntiteInconnue, ErreurValidation


@pytest.fixture
def connexion():
    with ConnexionSage() as cnx:
        yield cnx


def test_lire_un_tiers_existant(connexion):
    """lire() doit renvoyer les champs d'un tiers reellement present."""
    resultat = lire(connexion, "tiers", "BAGUES")
    assert resultat["succes"] is True
    assert resultat["donnees"]["CT_Num"] == "BAGUES"
    assert resultat["donnees"]["CT_Intitule"]


def test_lire_tiers_inexistant_leve_erreur(connexion):
    """lire() doit refuser une cle qui n'existe pas en base."""
    with pytest.raises(ErreurValidation):
        lire(connexion, "tiers", "NEXISTEPAS999")


def test_lire_sans_identifiant_leve_erreur(connexion):
    """lire() doit exiger un identifiant non vide."""
    with pytest.raises(ErreurValidation):
        lire(connexion, "tiers", "")


def test_lire_entite_inconnue_leve_erreur(connexion):
    """lire() doit refuser une entite absente du registre."""
    with pytest.raises(ErreurEntiteInconnue):
        lire(connexion, "entite_qui_n_existe_pas", "C001")


def test_lister_tiers_renvoie_tous_les_enregistrements(connexion):
    """lister() doit renvoyer autant de tiers que CompteTs.Count."""
    resultat = lister(connexion, "tiers")
    assert resultat["succes"] is True
    assert len(resultat["resultats"]) == connexion.base_comptable.CompteTs.Count
    assert all("CT_Num" in ligne for ligne in resultat["resultats"])


def test_creer_refuse_en_mode_lecture_seule(connexion):
    """creer() doit refuser d'ecrire quand MODE_LECTURE_SEULE=true (.env)."""
    with pytest.raises(ErreurValidation):
        creer(connexion, "tiers", {"CT_Num": "ZTEST01", "CT_Intitule": "Test"})


def test_modifier_refuse_en_mode_lecture_seule(connexion):
    """modifier() doit refuser d'ecrire quand MODE_LECTURE_SEULE=true (.env)."""
    with pytest.raises(ErreurValidation):
        modifier(connexion, "tiers", "BAGUES", {"CT_Intitule": "Modifie"})


def test_supprimer_tiers_non_supporte():
    """
    La suppression des tiers n'est pas supportee par l'API Sage installee
    (aucune methode Remove() trouvee, voir 00_analyse/04_VERIFICATION_COM.md).
    Verifie directement le registre plutot que d'appeler supprimer() (qui
    serait de toute facon bloque par le mode lecture seule en premier).
    """
    assert REGISTRE_ENTITES["tiers"]["suppression_supportee"] is False


def test_creer_sans_champ_obligatoire_leve_erreur(connexion):
    """creer() doit d'abord valider les champs avant toute autre logique."""
    with pytest.raises(ErreurValidation):
        creer(connexion, "tiers", {"CT_Num": "ZTEST02"})  # CT_Intitule manquant

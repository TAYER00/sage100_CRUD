"""
Tests de la connexion SQL en lecture seule a la base Sage BIJOU.

Necessite un fichier .env valide (voir .env.example) avec SQL_SERVER,
SQL_DATABASE, SQL_READONLY_USERNAME, SQL_READONLY_PASSWORD renseignes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from connexion.connexion_sql import ConnexionSQLLectureSeule


def test_connexion_sql_lecture_seule_reussit():
    """La connexion a la base Sage BIJOU doit pouvoir s'ouvrir."""
    connexion = ConnexionSQLLectureSeule()
    assert connexion.tester_connexion() is True


def test_lecture_quelques_tiers():
    """Une lecture simple sur F_COMPTET doit renvoyer des lignes exploitables."""
    connexion = ConnexionSQLLectureSeule()
    lignes = connexion.executer_lecture(
        "SELECT TOP 5 CT_Num, CT_Intitule, CT_Type FROM F_COMPTET"
    )
    assert isinstance(lignes, list)
    assert len(lignes) > 0
    assert "CT_Num" in lignes[0]


def test_executer_lecture_refuse_ecriture():
    """Une requete qui n'est pas un SELECT doit etre rejetee avant execution."""
    connexion = ConnexionSQLLectureSeule()
    try:
        connexion.executer_lecture("DELETE FROM F_COMPTET")
        assert False, "Une exception ValueError etait attendue"
    except ValueError:
        pass

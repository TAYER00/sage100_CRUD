"""
Configuration centralisee du projet sage_Conex_CRUD.

Lit les parametres depuis le fichier .env (non versionne - voir
.env.example pour le modele) et les expose via des classes simples, sans
aucune logique metier.

La partie "connexion SQL en lecture seule" reprend le pattern deja ecrit
et teste dans get_json_from_sage/config.py sur cette meme base (BIJOU),
volontairement limite ici au compte en lecture seule (BIJOU_READONLY) :
ce projet ne doit jamais ecrire directement en SQL (prompt_2.txt section 8).
"""

import os

from dotenv import load_dotenv

load_dotenv()


class ConfigurationSage:
    """Parametres de connexion aux objets metiers Sage 100 (COM)."""

    CHEMIN_BASE_COMPTABLE = os.getenv("SAGE_CHEMIN_BASE_COMPTABLE", "")
    CHEMIN_BASE_COMMERCIALE = os.getenv("SAGE_CHEMIN_BASE_COMMERCIALE", "")
    UTILISATEUR = os.getenv("SAGE_UTILISATEUR", "")
    MOT_DE_PASSE = os.getenv("SAGE_MOT_DE_PASSE", "")

    @classmethod
    def valider(cls):
        """Leve ValueError si le chemin de la base comptable est manquant."""
        if not cls.CHEMIN_BASE_COMPTABLE:
            raise ValueError(
                "SAGE_CHEMIN_BASE_COMPTABLE manquant dans le fichier .env."
            )


class ConfigurationSQLLectureSeule:
    """
    Parametres de connexion directe a la base SQL Server de Sage 100
    (BIJOU), strictement en LECTURE SEULE (compte db_datareader).

    Reserve a la verification de donnees et aux tables sans objet metier
    dedie (ex: F_CATEGCOMPT) - voir 00_analyse/02_ARCHITECTURE_PROPOSEE.md.
    """

    SERVEUR = os.getenv("SQL_SERVER", "")
    BASE = os.getenv("SQL_DATABASE", "BIJOU")
    UTILISATEUR = os.getenv("SQL_READONLY_USERNAME", "")
    MOT_DE_PASSE = os.getenv("SQL_READONLY_PASSWORD", "")

    @classmethod
    def valider(cls):
        """Leve ValueError si un parametre de connexion obligatoire manque."""
        requis = [cls.SERVEUR, cls.BASE, cls.UTILISATEUR, cls.MOT_DE_PASSE]
        if not all(requis):
            raise ValueError(
                "Configuration SQL (lecture seule) incomplete. Verifiez "
                "SQL_SERVER / SQL_DATABASE / SQL_READONLY_USERNAME / "
                "SQL_READONLY_PASSWORD dans le fichier .env."
            )


def mode_lecture_seule_actif() -> bool:
    """
    Indique si le mode lecture seule est actif (prompt_2.txt section 8 :
    "Prevoir un mode lecture seule pour les premiers tests"). Quand actif,
    creer()/modifier()/supprimer()/creer_document() doivent refuser de
    s'executer - seuls lire() et lister() restent autorises.
    """
    return os.getenv("MODE_LECTURE_SEULE", "true").strip().lower() == "true"

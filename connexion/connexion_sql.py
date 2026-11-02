"""
Connexion directe a la base SQL Server de Sage 100 (BIJOU), strictement en
LECTURE SEULE.

Pattern repris de get_json_from_sage/services/sage_client.py (deja ecrit
et teste sur cette meme base), adapte ici pour n'exposer QUE la lecture
(executer_lecture) : pas de methode d'ecriture, conformement a la regle de
prompt_2.txt section 8 ("Ne jamais modifier directement les tables Sage ...
privilegier les methodes officielles du SDK"). Les ecritures passent par
les objets metiers (voir connexion_sage.py, a venir).

Utilise par defaut le compte BIJOU_READONLY (role db_datareader), jamais
le compte "sa" utilise par get_json_from_sage.
"""

import pyodbc

from config.configuration import ConfigurationSQLLectureSeule
from gestion_erreurs.exceptions import ErreurConnexion


class ConnexionSQLLectureSeule:
    """Execute des requetes SELECT en lecture seule sur la base Sage BIJOU."""

    def __init__(self):
        ConfigurationSQLLectureSeule.valider()
        self._chaine_connexion = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={ConfigurationSQLLectureSeule.SERVEUR};"
            f"DATABASE={ConfigurationSQLLectureSeule.BASE};"
            f"UID={ConfigurationSQLLectureSeule.UTILISATEUR};"
            f"PWD={ConfigurationSQLLectureSeule.MOT_DE_PASSE};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=10;"
        )

    def tester_connexion(self) -> bool:
        """
        Objectif : verifier que la connexion a la base Sage BIJOU est possible.

        Parametres : aucun.

        Retour : True si la connexion s'ouvre et qu'une requete minimale
        ("SELECT 1") reussit.

        Validations : aucune (c'est le test le plus basique).

        Erreurs possibles : ErreurConnexion si pyodbc ne parvient pas a
        ouvrir la connexion (serveur injoignable, identifiants invalides...).

        Exemple :
            ConnexionSQLLectureSeule().tester_connexion()
        """
        try:
            with pyodbc.connect(self._chaine_connexion, timeout=10) as connexion:
                connexion.cursor().execute("SELECT 1")
            return True
        except pyodbc.Error as erreur:
            raise ErreurConnexion(
                f"Connexion a la base Sage impossible : {erreur}"
            ) from erreur

    def executer_lecture(self, requete: str, parametres=None) -> list[dict]:
        """
        Objectif : executer une requete SELECT et retourner les resultats.

        Parametres :
            requete (str) : la requete SQL, qui doit commencer par SELECT.
            parametres (list, optionnel) : valeurs pour les "?" de la requete.

        Retour : une liste de dictionnaires (une entree de dictionnaire par
        colonne, une entree de liste par ligne retournee).

        Validations : refuse toute requete qui ne commence pas par SELECT
        (leve ValueError) - cette classe ne doit jamais ecrire.

        Erreurs possibles : ErreurConnexion si la requete echoue cote SQL
        Server (table inexistante, droits insuffisants...).

        Exemple :
            connexion = ConnexionSQLLectureSeule()
            connexion.executer_lecture(
                "SELECT CT_Num, CT_Intitule FROM F_COMPTET WHERE CT_Type = ?",
                [0],
            )
        """
        if not requete.strip().upper().startswith("SELECT"):
            raise ValueError(
                "[VALIDATION] Seules les requetes SELECT sont autorisees "
                "par ConnexionSQLLectureSeule."
            )

        try:
            with pyodbc.connect(self._chaine_connexion, timeout=10) as connexion:
                curseur = connexion.cursor()
                curseur.execute(requete, parametres or [])
                colonnes = [colonne[0] for colonne in curseur.description]
                return [dict(zip(colonnes, ligne)) for ligne in curseur.fetchall()]
        except pyodbc.Error as erreur:
            raise ErreurConnexion(
                f"Erreur de lecture sur la base Sage : {erreur}"
            ) from erreur

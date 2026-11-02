"""
Connexion aux objets metiers Sage 100 (COM), base comptable.

IMPORTANT - API reellement verifiee sur ce poste (voir
00_analyse/04_VERIFICATION_COM.md pour le detail complet de la verification) :

    ProgID = "CPTA.Base.18"   (bibliotheque C:\\Program Files (x86)\\Common
    Files\\Sage\\CptaAx.dll)

Ce ProgID NE correspond PAS aux noms "BSCPTAApplication100c"/"IBOTiers3"
decrits dans docs/V12_Sage 100cloud Objets metiers v1220.pdf : cette
documentation decrit une autre famille d'API (IBO*), qui n'est pas
enregistree sur ce poste. L'inspection directe de la bibliotheque de types
COM installee (pythoncom.LoadTypeLib) et un test de connexion reel contre
la base Bijou SA ont permis de verifier la veritable API disponible ici :
la famille historique "CPTA" (CptaAx.dll / Maestria.exe), conformement a la
regle de prompt_2.txt ("ne pas inventer de methodes ou de proprietes du SDK
Sage, verifier les noms exacts").

Piege verifie : l'acces dynamique (win32com.client.Dispatch) echoue sur les
proprietes de collection (ex: CompteTs) avec l'erreur COM "Membre
introuvable". Seule la liaison anticipee
(win32com.client.gencache.EnsureDispatch, qui genere un wrapper Python a
partir de la bibliotheque de types) fonctionne - confirme par test reel.
"""

import win32com.client

from config.configuration import ConfigurationSage
from gestion_erreurs.exceptions import ErreurConnexion, ErreurSDKSage

PROG_ID_BASE_COMPTABLE = "CPTA.Base.18"


class ConnexionSage:
    """
    Ouvre/ferme la base comptable Sage 100 (objets metiers COM, famille
    CPTA) et expose l'objet "Base" ouvert, dont les services (ex:
    service_tiers.py, a venir a l'etape 3) liront les collections
    (CompteTs, CompteGs...) et les methodes de lecture
    (ReadCompteTNumero, QueryCompteTTypeOrderNumero...).
    """

    def __init__(self):
        ConfigurationSage.valider()
        self._base = None

    @property
    def est_ouverte(self) -> bool:
        """Indique si la base comptable est actuellement ouverte."""
        return self._base is not None

    def ouvrir(self):
        """
        Objectif : ouvrir la base comptable Sage 100 via COM.

        Parametres : aucun - lit ConfigurationSage.CHEMIN_BASE_COMPTABLE
        (fichier .env).

        Retour : aucun. L'etat ouvert est conserve dans self._base et
        accessible via la propriete base_comptable.

        Validations : la configuration doit etre valide (leve deja fait
        dans __init__ via ConfigurationSage.valider()).

        Erreurs possibles :
            ErreurSDKSage : le ProgID "CPTA.Base.18" n'est pas enregistre
                sur ce poste (objets metiers Sage non installes).
            ErreurConnexion : l'appel a Open() a echoue (chemin .mae
                invalide, base deja verrouillee par un autre process...).

        Exemple :
            connexion = ConnexionSage()
            connexion.ouvrir()
            ...
            connexion.fermer()
        """
        try:
            base = win32com.client.gencache.EnsureDispatch(PROG_ID_BASE_COMPTABLE)
        except Exception as erreur:
            raise ErreurSDKSage(
                f"Impossible d'instancier {PROG_ID_BASE_COMPTABLE} "
                f"(objets metiers Sage 100 non installes/enregistres sur "
                f"ce poste ?) : {erreur}"
            ) from erreur

        try:
            base.Open(ConfigurationSage.CHEMIN_BASE_COMPTABLE)
        except Exception as erreur:
            raise ErreurConnexion(
                "Connexion a la base Sage impossible "
                f"({ConfigurationSage.CHEMIN_BASE_COMPTABLE}) : {erreur}"
            ) from erreur

        self._base = base

    def fermer(self):
        """
        Objectif : fermer proprement la base comptable si elle est ouverte.

        Parametres : aucun.

        Retour : aucun.

        Erreurs possibles : aucune levee - si Close() echoue cote COM,
        l'erreur est ignoree pour garantir que la reference est bien
        liberee (self._base = None) dans tous les cas (voir
        prompt_2.txt section 7 : gestion de la memoire des objets).

        Exemple :
            connexion.fermer()
        """
        if self._base is not None:
            try:
                self._base.Close()
            except Exception:
                pass
            finally:
                self._base = None

    @property
    def base_comptable(self):
        """
        Objectif : donner acces a l'objet COM "Base" ouvert, pour que les
        services (etape 3+) puissent lire ses collections/methodes
        (CompteTs, ReadCompteTNumero, QueryCompteTTypeOrderNumero...).

        Retour : l'objet COM Base (wrapper genere par gencache).

        Erreurs possibles : ErreurConnexion si ouvrir() n'a pas encore ete
        appele.
        """
        if self._base is None:
            raise ErreurConnexion(
                "La connexion Sage n'est pas ouverte (appeler ouvrir() "
                "avant d'acceder a base_comptable)."
            )
        return self._base

    def __enter__(self):
        self.ouvrir()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.fermer()
        return False

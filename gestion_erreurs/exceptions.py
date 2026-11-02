"""
Exceptions dediees au projet et aides pour les messages en francais
([SUCCES] / [ERREUR] / [VALIDATION]), comme demande dans prompt_2.txt
section 6.

Regle importante (prompt_2.txt section 6) : un message [SUCCES] ne doit
JAMAIS etre affiche avant que l'operation ait ete reellement confirmee par
Sage (ex: apres un Write()/WriteDefault()/Remove() qui n'a pas leve
d'exception, voire apres une relecture de controle).
"""


class ErreurSageConexCRUD(Exception):
    """Classe de base pour toutes les erreurs de ce projet."""


class ErreurConnexion(ErreurSageConexCRUD):
    """La connexion a Sage (objets metiers ou SQL) a echoue."""


class ErreurEntiteInconnue(ErreurSageConexCRUD):
    """L'entite demandee (ex: 'tiers', 'article') n'existe pas dans le registre."""


class ErreurValidation(ErreurSageConexCRUD):
    """Un champ obligatoire manque, une cle est invalide, ou un doublon existe."""


class ErreurSDKSage(ErreurSageConexCRUD):
    """
    Encapsule une erreur COM/pywin32 brute levee par le SDK Sage, pour
    eviter de propager directement une exception COM peu lisible.
    """


def message_succes(texte: str) -> str:
    """Formate un message de succes standard : '[SUCCES] <texte>'."""
    return f"[SUCCES] {texte}"


def message_erreur(texte: str) -> str:
    """Formate un message d'erreur standard : '[ERREUR] <texte>'."""
    return f"[ERREUR] {texte}"


def message_validation(texte: str) -> str:
    """Formate un message de validation standard : '[VALIDATION] <texte>'."""
    return f"[VALIDATION] {texte}"

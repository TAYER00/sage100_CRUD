"""
Schemas Pydantic des corps de requete JSON acceptes par l'API.

Les entites restant generiques (registre d'entites, voir
crud/registre_entites.py), les champs eux-memes ne sont pas fixes au
niveau du schema : "donnees" est un dictionnaire libre dont les cles
doivent correspondre aux noms de colonnes Sage de l'entite visee (ex:
CT_Num, CT_Intitule, CT_Type, CG_NumPrinc pour "tiers").
"""

from typing import Any, Dict

from pydantic import BaseModel, Field


class CorpsCreation(BaseModel):
    """Corps JSON attendu pour POST /entites/{entite}."""

    donnees: Dict[str, Any] = Field(
        ...,
        description="Champs Sage a renseigner (ex: CT_Num, CT_Intitule, CT_Type, CG_NumPrinc pour 'tiers').",
        examples=[{"CT_Num": "C001", "CT_Intitule": "Client Test", "CT_Type": 0, "CG_NumPrinc": "4110000"}],
    )


class CorpsModification(BaseModel):
    """Corps JSON attendu pour PUT /entites/{entite}/{identifiant}."""

    donnees: Dict[str, Any] = Field(
        ...,
        description="Champs Sage a modifier (seuls les champs fournis sont modifies).",
        examples=[{"CT_Intitule": "Client Modifie"}],
    )

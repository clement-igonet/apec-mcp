"""APEC MCP Server — wraps the APEC candidate-profile REST API."""
from __future__ import annotations

import asyncio
import os
from typing import Any

from fastmcp import FastMCP

from apec_mcp import client as apec

mcp = FastMCP(
    name="APEC",
    instructions=(
        "Tools to manage an APEC candidate profile. "
        "Always call get_profile first to obtain the current profile object, "
        "then pass the (optionally modified) object to any update_* tool. "
        "All update endpoints require the complete profile body — never send partial objects."
    ),
)


# ---------------------------------------------------------------------------
# Identification
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_user_info() -> dict:
    """Return the currently authenticated APEC user (name, email, account numbers)."""
    return await apec.get("/cms/webservices/identification/apecuser")


# ---------------------------------------------------------------------------
# Profile — read
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_profile() -> dict:
    """
    Return the full candidate profile for the configured account.

    The returned object is the canonical body required by all update_* tools.
    Read the profile, modify only the fields you need, then pass the full
    object back to the relevant update tool.
    """
    aid = apec.account_id()
    return await apec.get(
        f"/cms/webservices/profilCadre/{aid}/complete",
        params={"idCompteCadre": aid},
    )


@mcp.tool()
async def get_profile_stats() -> dict:
    """Return profile view statistics: total views, publication duration, and views trend."""
    pid = apec.profile_id()
    views, duration, trend = await asyncio.gather(
        apec.get(f"/cms/webservices/profilVu/{pid}/nombreVuesDepuisPublication"),
        apec.get(
            f"/cms/webservices/profilVu/{pid}/dureePublication",
            params={"idProfilCadre": pid},
        ),
        apec.get(
            f"/cms/webservices/profilVu/{pid}/tendanceVues",
            params={"idProfilCadre": pid},
        ),
    )
    return {"total_views": views, "duration_days": duration, "trend": trend}


@mcp.tool()
async def get_cv_files() -> list:
    """List all CV files uploaded to the account."""
    return await apec.get("/cms/webservices/cv/cvFichiersByIdCompte")


@mcp.tool()
async def get_unread_messages_count() -> int:
    """Return the number of unread recruiter messages in the profile inbox."""
    aid = int(apec.account_id())
    return await apec.post(
        "/cms/webservices/echangeProfil/count",
        body={
            "criteres": {
                "idCompteCadre": aid,
                "suppressionCadre": False,
                "messageLu": False,
            }
        },
    )


# ---------------------------------------------------------------------------
# Profile — validate & update
# ---------------------------------------------------------------------------


@mcp.tool()
async def validate_section(profile: dict, section: str) -> dict:
    """
    Validate a profile section before saving.

    Args:
        profile: Full profile object (from get_profile).
        section: Section name — EXPERIENCES_FORMATIONS or PORTFOLIOS.

    Returns:
        Validation result (empty dict means valid).
    """
    return await apec.post(
        f"/cms/webservices/profilCadre/validation/{section}", body=profile
    )


@mcp.tool()
async def update_experiences_formations(profile: dict) -> Any:
    """
    Save work experiences and education in the profile.

    Modify these fields on the profile object before calling:
      experiencesCles — list of work experiences:
        {intitulePoste, idNomFonction, idNomMetier, dateEntree (ISO), dateSortie (ISO),
         nomEntreprise, expNonCadre, numeroOrdre, audit}
      formationsCles — list of education entries:
        {intituleFormation, dateEntree (ISO), dateSortie (ISO),
         idNomDiscipline, idNomNiveau, organismeFormation, numeroOrdre, audit}

    Args:
        profile: Full profile object with updated experiencesCles / formationsCles.
    """
    return await apec.post(
        "/cms/webservices/profilCadre/updateExperiencesEtFormations", body=profile
    )


@mcp.tool()
async def update_informations_complementaires(profile: dict) -> Any:
    """
    Save job-search preferences: sectors, functions, contract types, company sizes,
    work-time preferences, work modes, desired locations, and salary expectation.

    Modify these fields on the profile object before calling:
      souhaitsSecteurs, souhaitsFonctions, souhaitsContrats, souhaitsEnts,
      souhaitsTemps, souhaitsModes, souhaitsLieux,
      metierSouhaite, remunerationMinimale, idNomAnneesExperience,
      idNomDelaiDisponibilite, objectifProfessionnel.

    Args:
        profile: Full profile object with updated preference fields.
    """
    return await apec.post(
        "/cms/webservices/profilCadre/updateInformationsComplementaires", body=profile
    )


@mcp.tool()
async def update_atouts(profile: dict) -> Any:
    """
    Save skills (competences) and strengths (atouts).

    Modify these fields on the profile object before calling:
      competences — list of competence objects:
        {libelle, type (LANGUE|SAVOIR_ETRE|TECHNIQUE|METIER),
         idNomCompetence, idNomNiveau, miseEnAvant, idProfilCadre, audit}
      atouts — list of free-text strength strings.

    Args:
        profile: Full profile object with updated competences / atouts.
    """
    return await apec.post(
        "/cms/webservices/profilCadre/updateAtouts", body=profile
    )


@mcp.tool()
async def update_carte_de_visite(profile: dict) -> Any:
    """
    Save the candidate's business-card section: personal info, contact details,
    LinkedIn URL, photo, and salary settings.

    Modify these fields on the profile object before calling:
      nom, prenom, adresseEmail, numeroTelephoneMobile,
      lienLinkedin, remunerationMinimale, indicateurMasquerSalaire,
      adressePostale, photo.

    Args:
        profile: Full profile object with updated contact / personal fields.
    """
    return await apec.post(
        "/cms/webservices/profilCadre/carteDeVisite", body=profile
    )


# ---------------------------------------------------------------------------
# Search / autocomplete
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_metiers(q: str, max_results: int = 50) -> list:
    """
    Autocomplete search for APEC job titles (métiers / fonctions).

    Args:
        q: Search string (e.g. "Cloud", "Data scientist").
        max_results: Maximum suggestions to return (default 50).
    """
    return await apec.get(
        "/cms/webservices/autocompletion/distinctMetierAutocomplete",
        params={"q": q, "max": max_results, "byLeftAndRight": "false"},
    )


@mcp.tool()
async def autocomplete(q: str) -> list:
    """
    General-purpose APEC autocomplete (job titles, skills, locations, …).

    Args:
        q: Search string.
    """
    return await apec.get(
        "/cms/webservices/autocompletion/autocomplete",
        params={"q": q, "byLeftAndRight": "false"},
    )


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_metier_organisation(id_nom_metier: int) -> dict:
    """
    Return the APEC taxonomy node for a given métier ID.

    Args:
        id_nom_metier: Numeric métier ID (e.g. 599791 for "Cloud architect").
    """
    return await apec.get(
        f"/cms/webservices/referentielstatique/fonctions/metiers/{id_nom_metier}/organisation",
        params={"idNomMetier": id_nom_metier},
    )


@mcp.tool()
async def get_reference_lists(codes: list[str]) -> list:
    """
    Return reference/enum values for one or more APEC code lists.

    Common codes:
      CANDIDAPEC_NIVEAU_EXPERIENCE  — years-of-experience levels
      CANDIDAPEC_TYPE_CONTRAT       — contract types (CDI, CDD, …)
      CANDIDAPEC_SECTEUR_ACTIVITE   — activity sectors
      CANDIDAPEC_FONCTION           — job functions / métiers
      CANDIDAPEC_NIVEAU_FORMATION   — education levels
      CANDIDAPEC_MODE_TRAVAIL       — work modes (remote, on-site, hybrid)
      CANDIDAPEC_TAILLE_ENTREPRISE  — company sizes
      CANDIDAPEC_DISCIPLINE         — academic disciplines
      LISTE_MONDE                   — countries (idPays)

    Args:
        codes: List of presentation code strings to fetch.
    """
    return await apec.post(
        "/cms/webservices/referentielstatique/presentations/visuels/liste/hierarchie",
        body={"codesPresentations": codes},
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "sse")
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8080"))

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()

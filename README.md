# APEC MCP Server

MCP (Model Context Protocol) server that exposes the APEC candidate-profile API as tools for any MCP-compatible AI assistant.

---

## API Analysis

### API Type

**Proprietary REST / JSON over HTTPS.**  
Not publicly documented. Discovered via browser network capture (HAR files).  
Base URL: `https://www.apec.fr/cms/webservices/`

### Authentication

Cookie-based session auth — no OAuth, no API key.  
Required cookies (obtained by logging in on apec.fr):

| Cookie | Purpose | Lifetime |
|--------|---------|----------|
| `JSESSIONID` | Server-side session (Java/Spring backend) | Session |
| `datadome` | Bot-detection token | Hours |
| `apec.user.cookie` | User identity (XML payload) | Long |
| `apec_activity_cookie` | Activity tracking | Long |
| `srv_id` | Load-balancer affinity | Session |

> **Action required:** When the server starts returning 401/403, copy fresh cookies from DevTools → Network → any `/cms/webservices/*` request → Cookie header, and update `.env`.

### Reflection / Introspection

There is no public API schema (no OpenAPI spec, no GraphQL introspection).  
The API was reverse-engineered from three browser sessions:

- `www.apec.fr.har` — initial profile creation
- `www2.apec.fr.har` — portfolio/strengths editing
- `www3.apec.fr.har` — full profile editing (business card, photo upload, reference data)

The backend appears to be a **Java Spring** application (JSESSIONID, Jahia CMS static assets).

---

## API Endpoints

### Profile

| Method | Path | Description |
|--------|------|-------------|
| GET | `/profilCadre/{idCompte}/complete` | Full profile (the canonical object) |
| POST | `/profilCadre/updateExperiencesEtFormations` | Save experiences + education |
| POST | `/profilCadre/updateInformationsComplementaires` | Save job-search preferences |
| POST | `/profilCadre/updateAtouts` | Save skills + strengths |
| POST | `/profilCadre/carteDeVisite` | Save personal / contact info |
| POST | `/profilCadre/validation/{SECTION}` | Validate before saving |
| GET | `/profilCadre/shouldDisplayEncart` | UI display flag |
| GET | `/profilCadre/photoUploadFolders` | Photo upload paths |

### Stats

| Method | Path | Description |
|--------|------|-------------|
| GET | `/profilVu/{idProfil}/nombreVuesDepuisPublication` | Total profile views |
| GET | `/profilVu/{idProfil}/dureePublication` | Days since publication |
| GET | `/profilVu/{idProfil}/tendanceVues` | Views trend (float) |
| POST | `/echangeProfil/count` | Unread recruiter messages |
| POST | `/panierProfil/countInterlocuteursRetenir` | Saved contacts count |

### Search / Autocomplete

| Method | Path | Description |
|--------|------|-------------|
| GET | `/autocompletion/distinctMetierAutocomplete` | Job-title search |
| GET | `/autocompletion/autocomplete` | General search |

### Reference Data

| Method | Path | Description |
|--------|------|-------------|
| POST | `/referentielstatique/presentations/visuels/liste/hierarchie` | Enum lists (869 entries) |
| GET | `/referentielstatique/fonctions/metiers/{id}/organisation` | Métier taxonomy node |
| GET | `/referentielstatique/presentations/code/LISTE_MONDE/visuels` | Country list |

### Identification & CV

| Method | Path | Description |
|--------|------|-------------|
| GET | `/identification/apecuser` | Current user info |
| GET | `/cv/cvFichiersByIdCompte` | Uploaded CV files |
| GET | `/pushRecoOffre/abonnement/cadre/{id}` | Job-recommendation subscription |

---

## Data Model (TypeSpec)

```typespec
import "@typespec/rest";
import "@typespec/http";

using TypeSpec.Rest;
using TypeSpec.Http;

// ── Shared ──────────────────────────────────────────────────────────────

model Audit {
  dateCreation: int64;        // epoch ms
  dateModification: int64 | null;
  utilisateurCreation: string;
  utilisateurModification: string | null;
}

// ── Reference / enum entries ─────────────────────────────────────────────

model ReferenceItem {
  codePresentation: string;
  idNomenclature: int64;
  codeNomenclature: string;
  idOrganisation: int64;
  idOrganisationParent: int64 | null;
  libelle: string;
  niveau: int32;
  ordre: int32;
}

// ── Sub-models ───────────────────────────────────────────────────────────

model Experience {
  intitulePoste: string;
  idNomFonction: int64;
  idNomMetier: int64;
  dateEntree: string;           // ISO 8601
  dateSortie: string | null;
  nomEntreprise: string;
  expNonCadre: boolean;
  numeroOrdre: int32;
  audit: Audit;
}

model Formation {
  intituleFormation: string;
  dateEntree: string;           // ISO 8601
  dateSortie: string | null;
  idNomDiscipline: string;
  idNomNiveau: string;
  organismeFormation: string | null;
  numeroOrdre: int32;
  audit: Audit;
}

enum CompetenceType {
  LANGUE,
  SAVOIR_ETRE,
  TECHNIQUE,
  METIER,
}

model Competence {
  libelle: string;
  type: CompetenceType;
  idNomCompetence: int64;
  idNomNiveau: int64 | null;
  miseEnAvant: boolean;
  idProfilCadre: int64;
  audit: Audit;
  id: int64;
}

model AdressePostale {
  adresseNumeroEtVoie: string;
  adresseCodePostal: string;
  adresseVille: string;
  adresseBatimentImmResidence: string | null;
  adresseComplementAdresse: string | null;
  idPays: int64;
  audit: Audit;
  id: int64;
}

model SouhaitSecteur   { idNomSecteurActivite: int64; audit: Audit; id: int64; }
model SouhaitFonction  { idNomFonction: int64; idNomMetier: int64; audit: Audit; id: int64; }
model SouhaitContrat   { idNomTypeContrat: int64; audit: Audit; id: int64; }
model SouhaitEntreprise{ idNomTailleEntreprise: int64; audit: Audit; id: int64; }
model SouhaitTemps     { idNomTempsTravail: int64; audit: Audit; id: int64; }
model SouhaitMode      { idNomModeTravail: int64; audit: Audit; id: int64; }
model SouhaitLieu      { idNomLieu: int64; distance: int32 | null; audit: Audit; id: int64; }

// ── Full profile ─────────────────────────────────────────────────────────

model ProfilCadre {
  id: int64;
  idProfilCadre: int64;
  idCompteCadre: int64;
  idNomStatut: int64;
  idNomStatutCandidat: int64;

  // Personal info
  idNomCivilite: int64;
  nom: string;
  prenom: string;
  dateNaissance: int64;           // epoch ms
  adressePostale: AdressePostale;
  adresseEmail: string;
  numeroTelephoneMobile: string;
  lienLinkedin: string | null;
  photo: string | null;

  // Professional summary
  metierSouhaite: string;
  objectifProfessionnel: string | null;
  pointsClesProfessionnels: string | null;
  idNomAnneesExperience: int64;
  idNomDelaiDisponibilite: int64;
  remunerationMinimale: float32;
  indicateurMasquerSalaire: boolean;
  pretPourRecrutement: boolean;

  // Preferences
  souhaitsSecteurs: SouhaitSecteur[];
  souhaitsFonctions: SouhaitFonction[];
  souhaitsContrats: SouhaitContrat[];
  souhaitsEnts: SouhaitEntreprise[];
  souhaitsTemps: SouhaitTemps[];
  souhaitsModes: SouhaitMode[];
  souhaitsLieux: SouhaitLieu[];

  // Experiences & formations
  experiencesCles: Experience[];
  formationsCles: Formation[];

  // Skills
  competences: Competence[];
  atouts: string[];
  portfolios: unknown[];

  // CV
  idCvFichier: int64 | null;

  // Completion indicators
  tauxRemplissage: int32;
  indicateurCompletCompetence: boolean;
  indicateurCompletCompMea: boolean;
  indicateurCompletPortfolio: boolean;

  // Versioning
  numeroVersion: int32;
  numeroVersionCadre: int32;
  audit: Audit;
  auditCadre: Audit;
}

// ── User identity ────────────────────────────────────────────────────────

model ApecUser {
  id: string;
  numeroCompte: string;
  nom: string;
  prenom: string;
  email: string;
  cadre: boolean;
  actif: boolean;
  token: string;
  sessionId: string;
}
```

---

## MCP Tools

| Tool | APEC endpoint | Description |
|------|--------------|-------------|
| `get_user_info` | GET `/identification/apecuser` | Authenticated user details |
| `get_profile` | GET `/profilCadre/{id}/complete` | Full profile (use as base for updates) |
| `get_profile_stats` | GET `/profilVu/…` × 3 | Views, duration, trend |
| `get_cv_files` | GET `/cv/cvFichiersByIdCompte` | Uploaded CVs |
| `get_unread_messages_count` | POST `/echangeProfil/count` | Unread recruiter messages |
| `validate_section` | POST `/profilCadre/validation/{SECTION}` | Validate before saving |
| `update_experiences_formations` | POST `/profilCadre/updateExperiencesEtFormations` | Experiences + education |
| `update_informations_complementaires` | POST `/profilCadre/updateInformationsComplementaires` | Job-search preferences |
| `update_atouts` | POST `/profilCadre/updateAtouts` | Skills + strengths |
| `update_carte_de_visite` | POST `/profilCadre/carteDeVisite` | Personal / contact info |
| `search_metiers` | GET `/autocompletion/distinctMetierAutocomplete` | Job-title autocomplete |
| `autocomplete` | GET `/autocompletion/autocomplete` | General search |
| `get_metier_organisation` | GET `/referentielstatique/fonctions/…` | Métier taxonomy |
| `get_reference_lists` | POST `/referentielstatique/…/hierarchie` | Enum reference data |

### Update pattern

All update endpoints require the **complete profile object** (not a partial patch).

```
profile = get_profile()
profile["experiencesCles"].append({...})
update_experiences_formations(profile)
```

---

## Key Use Case — Fill Profile from LinkedIn or CV

The intended end-to-end workflow:

```
1. [LinkedIn MCP] get_my_profile()           → raw LinkedIn data
   OR parse CV text (PDF / plain text)

2. [APEC MCP]     get_reference_lists([…])  → resolve enum IDs
                  search_metiers(q=…)        → find idNomMetier / idNomFonction

3. AI assistant maps fields:
     LinkedIn title      → metierSouhaite + experiencesCles[].intitulePoste
     LinkedIn positions  → experiencesCles[]
     LinkedIn education  → formationsCles[]
     LinkedIn skills     → competences[]
     LinkedIn location   → adressePostale + souhaitsLieux[]

4. [APEC MCP]     get_profile()                     → fetch current profile
                  update_experiences_formations(…)  → save
                  update_informations_complementaires(…)
                  update_atouts(…)
                  update_carte_de_visite(…)
```

---

## Setup & Run

### Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- Docker / Apple Container with Compose support

### Local development

```bash
cp .env.example .env
# Edit .env — paste fresh cookies from DevTools

uv sync
uv run apec-mcp               # SSE on http://localhost:8080/sse
# or
MCP_TRANSPORT=stdio uv run apec-mcp
```

### Docker (Apple Container / Socktainer)

```bash
# First run — build and generate lock file locally
uv lock
docker compose up --build
```

The MCP server is available at `http://localhost:8080/sse`.

### MCP client config

```json
{
  "mcpServers": {
    "apec": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

---

## Session Refresh

Cookies expire. When you see 401/403:

1. Open `https://www.apec.fr` → log in
2. DevTools → Network → any `/cms/webservices/*` request → Headers → Cookie
3. Copy the full `Cookie:` value into `.env` as `APEC_COOKIES=...`
4. `docker compose restart`

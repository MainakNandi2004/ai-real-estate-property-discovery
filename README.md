# AI-Powered Real Estate Property Discovery

An AI-powered real estate property discovery prototype that helps users find suitable properties using natural-language requirements. The system extracts structured property preferences from user queries and searches a PostgreSQL database to return matching properties through REST APIs.

## Overview

Traditional property search often requires users to manually select multiple filters, such as location, budget, and BHK configuration.

This project aims to simplify that process by allowing users to describe their requirements in natural language.

**Example query:**

> I want a 3 BHK apartment in New Town under 80 lakh with parking.

The system extracts the relevant requirements, converts them into structured search criteria, and queries the property database to find matching properties.

## Key Features

- **AI-based requirement extraction:** Extracts requirements such as BHK, budget, location, and amenities from natural-language queries.
- **Structured property search:** Searches property data stored in PostgreSQL.
- **Budget parsing:** Supports Indian budget expressions such as lakh and crore.
- **Property matching:** Applies backend search and matching logic to identify suitable configurations.
- **REST API:** Exposes property search functionality through FastAPI endpoints.
- **Input validation and error handling:** Handles insufficient requirements, extraction failures, and search errors.
- **Database migrations:** Uses Alembic to manage database schema changes.
- **Automated testing:** Includes tests for requirement extraction, search logic, API behavior, and error handling.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Backend framework | FastAPI |
| AI integration | Google Gemini API |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database migrations | Alembic |
| API format | REST / JSON |
| Testing | Pytest |
| Server | Uvicorn |
| Version control | Git and GitHub |

## System Architecture

```text
User Query
    |
    v
AI Requirement Extraction
    |
    v
Structured Requirements
(BHK, Budget, Location, Amenities)
    |
    v
FastAPI Backend
    |
    v
Property Search Service
    |
    v
PostgreSQL Database
    |
    v
Search and Matching Logic
    |
    v
Matching Property Results
    |
    v
JSON API Response
```

### How It Works

1. The user submits a property requirement in natural language.
2. The AI extraction layer identifies relevant requirements.
3. The extracted information is converted into structured search criteria.
4. The backend validates the criteria and invokes the property search service.
5. The search service queries the PostgreSQL database.
6. The matching properties and relevant match information are returned through the API.

**Design principle:** The AI interprets user requirements, while the database and backend search logic provide the actual property information. Property details are retrieved from structured data rather than invented by the language model.

## Project Structure

```text
real-estate-ai/
├── app/
│   ├── ai/
│   │   ├── llm_client.py
│   │   └── requirement_extraction.py
│   ├── api/
│   │   └── ai_search.py
│   ├── repositories/
│   ├── schemas/
│   │   └── ai_search.py
│   ├── services/
│   │   ├── extraction_service.py
│   │   └── ai_search_service.py
│   ├── main.py
│   └── config.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_ai_search.py
│   └── test_requirement_extraction.py
├── alembic/
├── alembic.ini
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

*The tree highlights the main components; the exact files may vary with the current repository version.*

## Getting Started

### Prerequisites

Install the following:

- Python 3.12
- PostgreSQL
- A Google Gemini API key
- Git

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd real-estate-ai
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -e ".[dev]"
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and configure the required values.

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/real_estate_ai
APP_ENV=development
DEBUG=true
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_configured_gemini_model
```

Replace the placeholders with your local database credentials and configured Gemini model.

**Security:** Never commit `.env`, API keys, or database passwords to GitHub.

### 5. Create the Database

Create a PostgreSQL database named `real_estate_ai`, then apply the database migrations:

```bash
python -m alembic upgrade head
```

Ensure that the database server is running and the connection string is correct before starting the application.

### 6. Start the API Server

```bash
python -m uvicorn app.main:app --reload
```

The application will be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- Database health check: `http://127.0.0.1:8000/health/db`

## API Usage

### AI Property Search

**Endpoint**

```http
POST /api/ai/search
Content-Type: application/json
```

**Request body**

```json
{
  "query": "I want a 3 BHK in New Town under 80 lakh with parking"
}
```

**Expected processing**

The AI extraction layer identifies the requested BHK configuration, location, budget, and parking preference. The backend then searches the available property data.

**Example response structure**

```json
{
  "status": "exact_matches",
  "query": "I want a 3 BHK in New Town under 80 lakh with parking",
  "result_count": 1,
  "results": [],
  "unmatched_requirements": [],
  "message": "Matching properties found."
}
```

The response above illustrates the API structure. Actual results depend on the records in the configured database and the search outcome.

### Test the API

1. Start the FastAPI server.
2. Open `http://127.0.0.1:8000/docs`.
3. Expand `POST /api/ai/search`.
4. Select **Try it out**.
5. Enter a property query in the request body.
6. Select **Execute** and inspect the actual response.

## Testing

Run the automated test suite with:

```bash
python -m pytest
```

The project includes tests covering AI requirement extraction, property search coordination, API responses, validation, and error handling.

## Current Scope

This repository focuses on the AI-powered property-search backend and its database integration.

The implemented backend provides a foundation for a future real-estate application with features such as a customer-facing interface, property details, lead management, and site-visit booking. These should be treated as future extensions unless they are implemented in the current version.

## Future Enhancements

- Customer-facing web or mobile application
- Property listing and detailed property pages
- Advanced filtering and ranking
- Customer enquiry and lead management
- Site-visit scheduling
- Administrative dashboard
- Improved property recommendations

## Author

**Mainak Nandi**

- GitHub: [MainakNandi2004](https://github.com/MainakNandi2004)
- LinkedIn: [Mainak Nandi](https://www.linkedin.com/in/mainak-599a90297/)

## License

A license has not yet been specified. Add an appropriate `LICENSE` file before distributing the project under an open-source license.

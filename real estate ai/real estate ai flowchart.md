# REAL ESTATE AI — MASTER DEVELOPMENT FLOW

## PROJECT OBJECTIVE

Build an AI-powered real-estate property discovery and lead-generation
system.

The AI must help users:
1. Describe their property requirements in natural language.
2. Understand and extract those requirements.
3. Search only the available property data.
4. Recommend relevant properties.
5. Explain why properties match the user's requirements.
6. Handle follow-up questions while maintaining conversation context.
7. Collect lead information when the user is interested.
8. Generate a structured lead summary.

IMPORTANT:
- Property data is manually maintained by the developer initially.
- The AI must NEVER invent property information.
- Property data is the source of truth.
- Search/matching logic must operate on the property data.
- The AI is responsible for understanding language, conversation,
  recommendations, and explanations.
- Do not build unnecessary features before completing the current phase.
- Keep the architecture modular so JSON can later be replaced by MySQL.


# MASTER SYSTEM FLOW

                    USER
                      |
                      v
             USER MESSAGE
                      |
                      v
            CONVERSATION MANAGER
                      |
                      v
             AI UNDERSTANDING
                      |
                      v
          REQUIREMENT EXTRACTION
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
         BHK       BUDGET      LOCATION
          |           |           |
          +-----------+-----------+
                      |
                      v
              AMENITIES / OTHER
                PREFERENCES
                      |
                      v
          REQUIREMENT VALIDATION
                      |
              +-------+-------+
              |               |
            INCOMPLETE       COMPLETE
              |               |
              v               v
        ASK CLARIFYING     PROPERTY
           QUESTION          SEARCH
                              |
                              v
                    MATCHING ENGINE
                              |
                              v
                    PROPERTY RANKING
                              |
                              v
                     MATCHED RESULTS
                              |
                              v
                    AI RECOMMENDATION
                              |
                              v
                    USER RESPONSE
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
       CONTINUE CHAT                     USER INTERESTED
             |                                 |
             v                                 v
      UPDATE CONTEXT                    SITE VISIT / LEAD
                                               |
                                               v
                                        COLLECT DETAILS
                                               |
                                               v
                                          SAVE LEAD
                                               |
                                               v
                                       AI LEAD SUMMARY


# PHASE 1 — DATA LAYER

Initial source of truth:

    data/properties.json

The developer manually maintains this data.

Each property/project should contain, where available:

- id
- project_name
- location
- city
- project_status
- configurations
- bhk
- area
- price
- price_unit
- amenities
- parking
- possession
- nearby_locations
- description
- images
- floor_plans
- rera_information
- other_verified_information

DATA RULE:

Never create fictional Rajwada property information.

If information is unavailable, store it as null/unknown rather than
inventing a value.

Future architecture:

    properties.json
          |
          v
       MySQL

The application should be written so that replacing JSON with MySQL
later does not require rewriting the AI logic.


# PHASE 2 — PROPERTY SEARCH ENGINE

Before using AI recommendations, implement deterministic property search.

Input:

    Structured user requirements

Example:

    {
      "bhk": 2,
      "max_budget": 7000000,
      "location": "South Kolkata",
      "amenities": ["parking"]
    }

Search flow:

    Requirements
         |
         v
    Load property data
         |
         v
    Filter BHK
         |
         v
    Filter budget
         |
         v
    Filter location
         |
         v
    Filter amenities
         |
         v
    Filter other requirements
         |
         v
    Matching properties


The search engine must return only properties that actually exist
in the property data.


# PHASE 3 — AI REQUIREMENT EXTRACTION

Input:

Natural-language user message.

Example:

"I need a 2 BHK under 70 lakh around South Kolkata with parking."

AI converts it into structured requirements:

    {
      "bhk": 2,
      "min_budget": null,
      "max_budget": 7000000,
      "location": "South Kolkata",
      "amenities": ["parking"],
      "other_preferences": []
    }

The extraction system must:

1. Understand natural language.
2. Extract known requirements.
3. Normalize values.
4. Avoid guessing missing information.
5. Identify ambiguous requirements.
6. Ask clarification questions when necessary.


# PHASE 4 — REQUIREMENT VALIDATION

After extraction:

    Are enough requirements available?
             |
       +-----+-----+
       |           |
      NO          YES
       |           |
       v           v
 Ask question   Search properties

Example:

User:

"I want a nice flat."

AI:

"Sure. What approximate budget are you considering, and how many
bedrooms would you prefer?"

Do not ask unnecessary questions if sufficient information is already
available.


# PHASE 5 — PROPERTY MATCHING

The matching engine receives structured requirements.

Example:

    User requirements
           |
           v
    Candidate properties
           |
           v
    Apply filters
           |
           v
    Calculate match factors
           |
           v
    Rank candidates
           |
           v
    Return top relevant properties


Possible matching factors:

- BHK match
- Budget match
- Location match
- Amenities match
- Area preference
- Possession/status preference
- Other explicit user requirements

IMPORTANT:

The ranking system must be explainable.

Do not present arbitrary percentages such as "97% match" unless a
clearly defined scoring system has been implemented and tested.


# PHASE 6 — AI RECOMMENDATION

The AI receives:

1. User requirements.
2. Actual matching properties.
3. Relevant property information.

The AI then generates a natural-language recommendation.

Example:

"I found three properties that fit your requirements. Project A is
particularly relevant because it is a 2 BHK within your stated budget
and includes parking."

IMPORTANT:

The AI must base factual claims on the supplied property data.

The AI must not invent:

- Prices
- Amenities
- Availability
- Locations
- Distances
- RERA information
- Possession dates
- Project specifications


# PHASE 7 — CONVERSATIONAL MEMORY

Maintain the current conversation context.

Example:

USER:
"I need a 2 BHK under 70 lakh."

AI:
"What location do you prefer?"

USER:
"South Kolkata."

AI must retain:

    BHK = 2
    MAX_BUDGET = 7000000
    LOCATION = South Kolkata

Then:

USER:
"Which ones have parking?"

AI should use the existing requirements and add:

    AMENITY = parking

Do not make the user repeat previous requirements unnecessarily.


# PHASE 8 — FOLLOW-UP QUESTIONS

The AI must support questions such as:

- "Which one is cheaper?"
- "Which one has parking?"
- "What about a 3 BHK?"
- "Show me something closer to the metro."
- "Which one has a swimming pool?"
- "Tell me more about the first project."

The AI must answer using available property data.

If required information does not exist:

    "I don't currently have verified information about that."


# PHASE 9 — NO-MATCH HANDLING

If no property exactly matches:

    Search
       |
       v
    Exact matches?
       |
    +--+--+
    |     |
   YES    NO
    |     |
    v     v
 Return   Search for
 results  reasonable alternatives
              |
              v
       Explain difference

Example:

"I couldn't find an exact match for a 3 BHK under ₹50 lakh in your
selected location. I found two nearby options, but both are above
your stated budget."

Never fabricate an exact match.


# PHASE 10 — PROPERTY DETAILS

When the user selects a property:

    Property result
          |
          v
    Property details

Display/return available:

- Project name
- Location
- Configuration
- Area
- Price
- Amenities
- Status
- Possession
- Images
- Floor plan
- RERA information
- Other verified details

Only show information actually available in the data source.


# PHASE 11 — LEAD GENERATION

If the user expresses interest:

    Property recommendation
            |
            v
    "Would you like to schedule
     a site visit or speak with
     an advisor?"
            |
       +----+----+
       |         |
      NO        YES
       |         |
       v         v
 Continue    Collect details


Lead fields initially:

- name
- phone
- email
- interested_project
- requirement
- budget
- preferred_date
- preferred_time
- conversation_summary


# PHASE 12 — AI LEAD SUMMARY

Convert the conversation into a concise structured summary.

Example:

    Customer:
    Rahul

    Requirement:
    2 BHK

    Budget:
    ₹60–70 lakh

    Location:
    South Kolkata

    Important requirement:
    Parking

    Interested project:
    Project A

    Site visit:
    Sunday

The summary must be generated only from information provided by
the customer and verified property data.


# PHASE 13 — API LAYER

After the AI engine works independently, expose it through an API.

Initial architecture:

    Frontend
       |
       v
    FastAPI
       |
       +------> AI Engine
       |
       +------> Search Engine
       |
       +------> Property Data
       |
       +------> Lead System


Potential endpoints:

    POST /api/chat
    POST /api/property-search
    GET  /api/properties
    GET  /api/properties/{id}
    POST /api/leads
    POST /api/site-visits


Do not build unnecessary endpoints before they are required.


# PHASE 14 — WEBSITE INTEGRATION

After Phase 1 is stable:

    Rajwada Website
          |
          v
       Frontend
          |
          v
       REST API
          |
          v
      AI Backend
          |
      +---+---+
      |       |
      v       v
      AI    Search
              |
              v
         Property Data


The AI assistant becomes a component inside the website.


# PHASE 15 — FUTURE DATABASE UPGRADE

Current:

    properties.json
         |
         v
      Search

Future:

    Admin Dashboard
          |
          v
        MySQL
          |
          v
    Search / AI System

The AI layer should remain independent from the storage layer.


# PHASE 16 — FUTURE FEATURES

Only after the core system is stable:

1. Laravel backend
2. MySQL production database
3. Admin dashboard
4. CRM integration
5. WhatsApp AI assistant
6. Site-visit automation
7. AI lead scoring
8. AI sales assistant
9. Voice AI
10. Analytics
11. Customer behaviour analysis
12. Marketing intelligence


# DEVELOPMENT RULES

1. Build incrementally.
2. Test every module before moving forward.
3. Do not write the entire project at once.
4. Do not introduce unnecessary frameworks.
5. Keep AI, search, data and API layers separate.
6. Never allow AI to invent factual property information.
7. Use verified data as the source of truth.
8. Keep secrets/API keys in environment variables.
9. Never hard-code API keys.
10. Keep code modular and documented.
11. Write tests for important search/matching logic.
12. Handle errors gracefully.
13. Keep the system easy to migrate from JSON to MySQL.
14. Build the simplest working version first.
15. Add complexity only when required.


# FINAL TARGET

The completed system should follow:

USER
  ↓
AI CONVERSATION
  ↓
REQUIREMENT EXTRACTION
  ↓
VALIDATION
  ↓
PROPERTY SEARCH
  ↓
MATCHING / RANKING
  ↓
AI RECOMMENDATION
  ↓
FOLLOW-UP CONVERSATION
  ↓
PROPERTY DETAILS
  ↓
LEAD / SITE VISIT
  ↓
AI LEAD SUMMARY
  ↓
API
  ↓
WEBSITE
  ↓
FUTURE CRM / MYSQL / WHATSAPP / ANALYTICS


# CURRENT DEVELOPMENT TARGET

DO NOT start with the complete system.

Start only with:

    1. Property data structure
    2. properties.json
    3. Property data validation
    4. Basic property search
    5. AI requirement extraction
    6. AI + property search
    7. AI recommendations
    8. Conversation context
    9. No-match handling
    10. Lead summary

Only after these work correctly should website integration begin.
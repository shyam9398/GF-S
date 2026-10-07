# IISCAE-Intelligent Indian Standards Context-Aware Engine
# AI-Powered Recommendation Engine for Identifying Applicable Indian Standards

An AI-powered procurement intelligence platform that analyzes procurement specifications and recommends applicable Indian Standards (BIS) with evidence, applicability validation, and traceable reasoning.

## 2. Problem Statement


Procurement officers often need to identify the correct Indian Standards applicable to a product or procurement specification.

Traditional identification requires manually reviewing procurement documents, searching multiple BIS resources, comparing technical requirements, and determining whether a standard is actually applicable.

This process can be time-consuming and may result in:

- Missed relevant standards
- Incorrect standard selection
- Keyword-based false matches
- Difficulty identifying related and normative standards
- Difficulty tracking amendments and lifecycle status
- Lack of traceable evidence for recommendations

The problem is to develop an intelligent system that can automatically understand procurement specifications and identify the most applicable Indian Standards.

## 3. Proposed Solution

We propose an **AI-Powered BIS Standards Recommendation Engine** designed specifically for procurement officers.

The system accepts a tender or procurement specification, extracts the product and technical requirements using AI, generates product-centric BIS search queries, retrieves relevant standards, and evaluates their applicability.

The system uses a combination of:

- Document understanding
- Semantic analysis
- BIS standards retrieval
- Product identity validation
- Standard role classification
- Applicability scoring
- Relationship analysis
- QCO / certification tracking
- Lifecycle validation
- Evidence-based recommendations

### Solution Flow


                                          Procurement Specification
                                                    ↓
                                            Document Extraction
                                                    ↓
                                          AI Semantic Understanding
                                                    ↓
                                            BIS Standards Search
                                                    ↓
                                            Candidate Standards
                                                    ↓
                                          Product & Role Validation
                                                    ↓
                                            Applicability Analysis
                                                    ↓
                                        Relationship & Evidence Analysis
                                                    ↓
                                          QCO / Lifecycle Validation
                                                    ↓
                                            Applicable BIS Standards

---

# 4. Key Features

### 📄 Smart Document Analysis
Extracts product, technical, performance, safety, material, and testing requirements from procurement documents.

### 🧠 Semantic Understanding
Uses AI to understand the meaning and context of procurement requirements instead of relying only on exact keywords.

### 🔎 BIS Standards Discovery
Generates concise product-centric queries and retrieves relevant BIS standards.

### 🎯 Applicability Validation
Evaluates standards using:

- Product Compatibility
- Semantic Similarity
- Application Match
- Technical Match
- Safety / Material Match

### 🛡️ Standard Role Gate
Identifies whether a standard is a:

- Product Specification
- Test Method
- Sampling Method
- Headform
- Material Specification
- Component Specification
- Installation Standard
- Safety Guide
- Related Product

This prevents supporting or testing standards from being incorrectly recommended as primary standards.

### 🔍 Product Identity Validation
Validates:

- Product Family
- Product Subtype
- Intended Application
- Intended Use
- Material
- Technical Purpose

### 🔗 Six-Way Classification

Standards are categorized as:

1. Primary Applicable
2. Normative References
3. Allied Standards
4. Related Supporting
5. Needs Verification
6. Not Applicable

### 🏛️ QCO / Certification Analysis
Identifies available certification and Quality Control Order information.

### 🔄 Lifecycle Tracking
Tracks available information such as:

- Active
- Withdrawn
- Superseded
- Reaffirmed
- Amendments
- Revision

### 🧾 Evidence-Based Recommendations
For each recommendation, the system provides:

- Standard Number
- Standard Title
- Applicability
- Score
- Reason
- Evidence
- Source
- Related Standards

### 👤 Procurement Officer Authentication
Secure login and signup using Supabase Auth with `.bis` usernames.

Example: procurement01.bis


---

# 5. System Architecture



                                                PROCUREMENT OFFICER
                                                       │
                                                       ▼
                                              Procurement Document
                                                       │
                                                       ▼
                                                    DOCLING
                                                       │
                                                       ▼
                                             Document Extraction
                                                       │
                                                       ▼
                                             GEMINI SEMANTIC AI
                                                       │
                                                       ▼
                                            Structured Requirements
                                                       │
                                                       ▼
                                                QUERY PLANNER
                                                       │
                                                       ▼
                                                BIS SEARCH API
                                                       │
                                                       ▼
                                              Candidate Standards
                                                       │
                                                       ▼
                                                DEDUPLICATION
                                                       │
                                                       ▼
                                            STANDARD ROLE GATE
                                                       │
                                                       ▼
                                          PRODUCT IDENTITY GATE
                                                       │
                                                       ▼
                                           APPLICABILITY ENGINE
                                                       │
                                                       ▼
                                      RELATIONSHIP & EVIDENCE ENGINE
                                                       │
                                                       ▼
                                           QCO / LIFECYCLE CHECK
                                                       │
                                                       ▼
                                           RECOMMENDATION ENGINE
                                                       │
                                                       ▼
                                                FINAL RESULTS


## 6. Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React + TypeScript + Vite | Responsive procurement officer interface |
| UI | Tailwind CSS | Clean and responsive enterprise UI |
| Backend | Python + FastAPI | API and analysis pipeline |
| Document Processing | Docling | Extracts structured text from procurement PDFs |
| AI / Semantic Analysis | Google Gemini API | Understands product and procurement requirements |
| Semantic Embeddings | Gemini Embeddings | Semantic comparison between requirements and standards |
| Retrieval Fallback | BM25 / Jaccard | Lightweight lexical matching fallback |
| BIS Integration | Live BIS Services | Retrieves current candidate Indian Standards |
| Applicability Engine | Python Rule Engine | Validates product compatibility and applicability |
| Certification / QCO | Official Gazette Data | Identifies mandatory, voluntary, and verification status |
| Database | PostgreSQL | Stores analyses, results, and evidence |
| Database Platform | Supabase | PostgreSQL database and authentication services |
| Authentication | Supabase Auth | Secure Procurement Officer authentication |
| Localization | IndicTrans2 / Indic Language Layer | Supports 22+ Indian languages |
| API Client | Axios | Frontend–backend communication |
| Backend Server | Uvicorn | ASGI server for FastAPI |
| Frontend Deployment | Vercel | Production frontend hosting |
| Backend Deployment | Render | Production FastAPI hosting |
| Version Control | Git + GitHub | Source control and collaboration |

### Why These Technologies?

- **React + TypeScript** → Fast and maintainable frontend.
- **FastAPI** → Lightweight and high-performance backend.
- **Docling** → Structured extraction from procurement documents.
- **Gemini** → Semantic understanding and requirement structuring.
- **Gemini Embeddings** → Semantic similarity between requirements and standards.
- **BM25** → Lightweight lexical fallback.
- **Supabase** → PostgreSQL database, authentication, and storage.
- **BIS Services** → Dynamic standards discovery instead of hardcoded standards.
- **Vercel** → Frontend deployment.
- **Render** → Backend deployment.

## 7. Current Approach vs Our Approach

| Aspect | Current / Traditional Approach | Our Approach |
|---|---|---|
| Standard Discovery | Manual searching across BIS resources | AI-assisted BIS standards discovery |
| Document Analysis | Manual reading of tender specifications | Automated Docling-based document extraction |
| Product Understanding | Keyword-based interpretation | Gemini-powered semantic product understanding |
| Search Strategy | Generic keyword searches | Product-centric query generation |
| Standard Selection | Manual comparison | Automated applicability evaluation |
| Product Identity | Broad keyword/category matching | Product type and subtype validation |
| False Matches | High risk of unrelated standards being selected | Product Compatibility Gate filters mismatches |
| Standard Role | Supporting standards can be confused with product standards | Standard Role Gate identifies functional role |
| Applicability | Mainly manual judgment | Deterministic + semantic applicability scoring |
| Related Standards | Difficult to identify systematically | 6-way standards classification |
| Certification | Checked separately/manual lookup | Integrated QCO and certification verification |
| Amendments & Versions | Can be overlooked | Lifecycle, reaffirmation, amendment and supersession tracking |
| Evidence | Limited traceability | Evidence-backed recommendations with source references |
| Uncertainty | Often hidden in manual results | `NEEDS_VERIFICATION` classification for uncertain cases |
| Processing | Time-consuming | Automated end-to-end analysis pipeline |
| Memory Usage | Can require heavy local ML/OCR models | Lightweight architecture using Docling + Gemini API + BM25 |
| Localization | Usually English-focused | 22+ Indian language localization layer |
| Output | Manual list of standards | Structured recommendation report with scores, evidence and relationships |
| Procurement Workflow | Fragmented tools and manual verification | Unified procurement intelligence platform |

## 8. Future Enhancements

- Multi-document procurement analysis
- Tender clause-level mapping
- Advanced BIS relationship graph
- Multilingual procurement document analysis
- Voice-based procurement assistant
- Automatic standard change notifications
- Advanced amendment comparison
- Procurement compliance risk scoring
- Human-in-the-loop verification
- Automated compliance report generation
- PDF recommendation report export
- Historical procurement analysis
- Organization-level procurement analytics
- Integration with enterprise procurement systems
- Continuous BIS standards monitoring

## 9. Reference Links

### 🚀 MVP Application

[Open MVP Application]( https://gf-s.vercel.app/)

### 🎥 Demo Video

[Watch Demo Video](https://drive.google.com/drive/folders/13O6MsQiBqMmyzyamgAGUDxpN7F-7oya2)

### 📂 Source Code

[GitHub Repository](https://github.com/shyam9398/GF-S)

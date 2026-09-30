# 🚀 JobPilot AI

**JobPilot AI** is an AI-powered job application assistant designed to automate and streamline the end-to-end job application workflow while keeping critical decisions under human control.

Instead of simply generating a resume with an LLM, JobPilot AI uses a multi-stage pipeline to analyze job descriptions, evaluate candidate-job compatibility, tailor application documents, validate AI-generated claims, prepare application forms, and assist with submission.

The system is designed around one key principle:

> **AI can assist with the application process, but it should never invent candidate information or make sensitive decisions on the user's behalf.**

---

## ✨ Key Features

### 📄 Master CV Parsing
- Upload a master CV in PDF or DOCX format.
- Extract structured candidate information including:
  - Skills
  - Education
  - Experience
  - Projects
  - Certifications
  - Languages
  - LinkedIn and GitHub links
- Uses the parsed **Candidate Profile as the source of truth** for later AI operations.

### 🔍 Job Analysis
- Analyzes job descriptions using AI.
- Extracts role requirements, technical skills, experience expectations, and other relevant information.
- Converts unstructured job descriptions into structured data.

### 🎯 Candidate–Job Matching
- Compares the Candidate Profile with job requirements.
- Generates an evidence-based match score.
- Identifies matching skills and potential gaps.

> The match percentage represents profile-to-job alignment, not the probability of being hired.

### 📝 AI-Powered CV Tailoring
- Generates a job-specific CV tailoring plan.
- Prioritizes relevant skills, projects, and experiences.
- Preserves the original facts from the Master CV.
- Avoids inventing new skills or experiences.

### 🛡️ CV Validation & Correction
AI-generated content is not trusted automatically.

JobPilot AI uses a validation pipeline:

```text
Tailored CV
     ↓
Validation Agent
     ↓
Issue Detected?
     ↓
Correction Agent
     ↓
Re-validation
     ↓
Approved CV
```

The validator checks generated claims against the Candidate Profile.

For example, if the candidate has experience **training a machine learning model**, the system prevents the AI from incorrectly upgrading that experience to **deploying a production ML system** without supporting evidence.

### 📑 Document Generation
Once validated, tailored documents can be generated as:

- DOCX
- PDF

The CV layout is designed to remain simple and ATS-friendly.

### ✉️ Cover Letter Generation
- Generates job-specific cover letters.
- Uses Candidate Profile and job information.
- Includes a separate validation and correction pipeline.
- Prevents unsupported candidate claims from being included.

### 📦 Application Package
Each application can contain:

```text
Application
├── Match Analysis
├── Tailored CV
│   ├── DOCX
│   └── PDF
├── Cover Letter
│   ├── DOCX
│   └── PDF
└── Validation Results
```

Before browser automation begins, the user reviews and approves the application package.

### 🔐 Approval & Integrity Checks
Approved documents are protected using SHA-256 hashes.

If an approved CV or cover letter changes afterward, JobPilot AI can detect the modification and invalidate the previous approval.

### 🌐 Application Form Inspection

JobPilot AI uses **Playwright** to inspect application forms and detect fields such as:

```text
Input
Textarea
Select
File Upload
Required Fields
```

The system then maps form fields to trusted data sources.

Example:

```text
Email
→ Candidate Profile

Resume
→ Approved CV

Cover Letter
→ Approved Cover Letter

Work Authorization
→ User Required
```

### 👤 Human-in-the-Loop Decisions

Sensitive or application-specific questions are never guessed by the AI.

Examples include:

- Work authorization
- Visa requirements
- Sponsorship
- Salary expectations
- Relocation
- Availability
- Demographic information
- Legal attestations

These fields require explicit user input.

### ⚙️ Deterministic Form Resolution

LLM-generated values are not directly inserted into application forms.

After AI determines what a field represents, a deterministic resolver retrieves the actual value from an approved source.

```text
AI Field Mapping
       ↓
Deterministic Resolver
       ↓
Trusted Data Source
       ↓
Form Value
```

This separates AI reasoning from the actual data submitted to the form.

### 🤖 Browser Automation
Playwright is used to:

- Inspect application forms
- Fill text fields
- Select options
- Upload CVs
- Upload cover letters
- Verify populated values
- Generate form previews
- Assist with final submission

The system verifies form values after filling instead of assuming that a browser action succeeded.

### ✅ Human Approval Before Submission

Document approval and submission approval are intentionally separated.

```text
Application Package
        ↓
Package Approval
        ↓
Form Preparation
        ↓
Form Verification
        ↓
Final User Approval
        ↓
Submission
```

The system also prevents duplicate submissions for the same application.

---

## 🧠 System Architecture

```text
                    ┌────────────────────┐
                    │     Master CV      │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ Candidate Profile  │
                    └─────────┬──────────┘
                              │
             ┌────────────────┴────────────────┐
             │                                 │
             ▼                                 ▼
     ┌───────────────┐                 ┌───────────────┐
     │ Job Analyzer  │                 │  Match Agent  │
     └───────┬───────┘                 └───────┬───────┘
             │                                 │
             └────────────────┬────────────────┘
                              ▼
                    ┌────────────────────┐
                    │ CV Tailoring Agent │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │    CV Validator    │
                    └─────────┬──────────┘
                              │
                        Issue detected
                              │
                              ▼
                    ┌────────────────────┐
                    │ Correction Agent   │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │ Document Generator │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │   Cover Letter     │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │ Package Approval   │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │  Form Inspection   │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │   Field Mapping    │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │  Value Resolver    │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │ Playwright Filling │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │ Form Verification  │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │   Final Approval   │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │     Submission     │
                    └────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic

### AI
- OpenAI API
- Structured Outputs
- Multi-agent workflow

### Browser Automation
- Playwright
- Chromium

### Document Processing
- python-docx
- pypdf
- LibreOffice

### Frontend
- React
- Vite
- React Router
- Axios
- Recharts
- Lucide React

### Infrastructure
- Docker
- Docker Compose

---

## 📁 Project Structure

```text
jobpilot-ai/
│
├── app/
│   ├── agents/
│   │   ├── cv_parser.py
│   │   ├── job_analyzer.py
│   │   ├── match_agent.py
│   │   ├── cv_tailoring_agent.py
│   │   ├── cv_validator.py
│   │   ├── cv_correction_agent.py
│   │   ├── cover_letter_agent.py
│   │   └── form_mapping_agent.py
│   │
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── config.py
│   ├── database.py
│   └── main.py
│
├── alembic/
│   └── versions/
│
├── desktop_agent/
│   └── jobpilot_browser_agent.py
│
├── frontend/
│   ├── public/
│   └── src/
│       ├── components/
│       ├── context/
│       ├── pages/
│       └── services/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── README.md
```

---

## 🔄 Application Workflow

A typical JobPilot AI workflow follows these steps:

```text
1. Upload Master CV
        ↓
2. Parse Candidate Profile
        ↓
3. Add Job
        ↓
4. Analyze Job Requirements
        ↓
5. Calculate Candidate–Job Match
        ↓
6. Generate Tailored CV
        ↓
7. Validate & Correct CV
        ↓
8. Generate Cover Letter
        ↓
9. Validate & Correct Cover Letter
        ↓
10. Review Application Package
        ↓
11. Approve Documents
        ↓
12. Inspect Application Form
        ↓
13. Resolve Required Fields
        ↓
14. Fill & Verify Form
        ↓
15. Final User Review
        ↓
16. Approve Submission
        ↓
17. Submit / Confirm
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/fatmanurakbas/jobpilot-ai.git
cd jobpilot-ai
```

### 2. Configure environment variables

Create a `.env` file based on `.env.example`.

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=your_database_url_here
OPENAI_MODEL=your_model_name_here
```

> Never commit your real `.env` file or API keys to Git.

### 3. Start the backend

Using Docker Compose:

```bash
docker compose up --build
```

The FastAPI API will be available at:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

### 4. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

---

## 🔒 Safety & Reliability Principles

JobPilot AI was designed around several safeguards:

- Candidate Profile is treated as the factual source of truth.
- AI-generated claims are validated before document generation.
- Unsupported claims can be automatically corrected.
- Sensitive application questions are not inferred.
- LLM-generated values are not directly trusted for form submission.
- Documents require explicit user approval.
- SHA-256 hashes detect modifications after approval.
- Form values are verified after browser automation.
- Final submission requires separate user approval.
- Duplicate submissions are prevented.

---

## 🧪 Demo Mode

For development and demonstration purposes, the repository includes a controlled test application form.

This allows the complete workflow to be demonstrated without submitting an application to a real company.

```text
Job Analysis
     ↓
CV Tailoring
     ↓
Validation
     ↓
Cover Letter
     ↓
Package Approval
     ↓
Form Inspection
     ↓
Form Filling
     ↓
Verification
     ↓
Final Approval
     ↓
Submission Test
```

This environment is intended for safely testing the automation pipeline.

---

## 🔮 Future Improvements

Potential future improvements include:

- Support for additional job platforms
- More advanced application tracking
- Improved browser review workflow
- Job discovery and recommendation
- Application analytics
- Enhanced multi-language CV support
- Additional form-field adapters
- More robust submission confirmation mechanisms

---

## 👩‍💻 Developer

**Fatma Nur Akbaş**

Computer Engineer focused on Artificial Intelligence, Machine Learning and Backend Development.

- GitHub: [fatmanurakbas](https://github.com/fatmanurakbas)
- LinkedIn: [Fatma Nur Akbaş](https://www.linkedin.com/in/fatmanurakbas/)

---

## ⚠️ Disclaimer

JobPilot AI is an experimental software project designed to assist with job application workflows.

Users should review all generated documents, form answers, and application details before submission. Automated interactions with third-party websites should only be used where permitted by the relevant website's terms and policies.

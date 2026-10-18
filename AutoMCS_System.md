# AutoMCS — Complete Website Project Specification

**Project Title:** AutoMCS — AI-Assisted Decimal Table Extraction, Labeling, Verification, and Dataset Management

**Brand:** **AutoMCS** by Puthivuth Chhoeun

**Frontend:** Next.js, React, TypeScript, Tailwind CSS, and shadcn/ui

**Backend:** Python, Django, and Django REST Framework

**Database:** PostgreSQL

**Primary Purpose:** To build a secure, professional research web application that automatically extracts decimal values from images and PDF documents, enables human verification and correction, evaluates extraction performance, and exports high-quality ground-truth datasets for research and future model training.

---

## 1. Project Overview

AutoMCS is a web-based application designed to reduce the amount of repetitive manual work required to label decimal values in tables. Users can upload individual images, multiple images, complete folders of images, or PDF documents. The application uses an AI extraction provider selected by the user to extract table contents into structured data.

The user can then compare the extracted results with the original documents, correct inaccurate values, approve verified labels, evaluate model performance, and export the corresponding original files and ground-truth data.

The application must support two AI extraction options:

1. **Gemini API:** A cloud-based extraction option using a configurable, vision-capable Gemini model.
2. **Local DeepSeek 1.5B:** A locally hosted DeepSeek-R1-Distill-Qwen-1.5B model, using OCR and table preprocessing when necessary to provide textual input to the model.

The local model manager must automatically detect missing model files, download them from a trusted model repository when configured to do so, validate them, load the model, and make it available for extraction.

The website must also be designed for future model training on a higher-performance GPU server.

The system must preserve all original documents, predictions, verified labels, database records, and model artifacts when the website is updated, redeployed, or replaced.

## 2. Main Objectives

The main objectives of AutoMCS are:

1. Automate decimal-value extraction from table images and PDFs.
2. Support individual image uploads, multi-image uploads, and complete image-folder imports.
3. Support batch AI extraction to reduce repetitive manual labeling.
4. Allow users to choose Gemini API or local DeepSeek 1.5B for each extraction job.
5. Preserve original table structure, including rows, columns, blank cells, and source document references.
6. Normalize final decimal values to exactly two decimal places.
7. Provide a manual labeling interface for correcting AI predictions or labeling data without AI.
8. Provide side-by-side comparison between original documents and extracted tables.
9. Maintain a reliable separation between AI predictions and approved ground-truth labels.
10. Evaluate extraction accuracy against verified data.
11. Export original documents together with corresponding JSON, CSV, or JSONL labels.
12. Support multiple independent projects without mixing their data.
13. Prepare the architecture for future model training and version management.
14. Keep model files, uploaded data, and the database in persistent storage.
15. Protect private research documents and data from unauthorized access.

## 3. Technology Stack

### Frontend

Use Next.js with TypeScript, React, Tailwind CSS, and shadcn/ui or equivalent accessible components.

The frontend is responsible for public pages, authentication screens, the dashboard, project management, document previews, editable tables, extraction controls, evaluation results, and dataset exports.

### Backend

Use Django and Django REST Framework for authentication, database operations, project isolation, file management, AI provider integration, decimal normalization, evaluation, export generation, and job management.

All security-sensitive operations must be validated by the backend rather than relying on frontend restrictions.

### Database

Use PostgreSQL to store users, projects, document metadata, extracted tables, predictions, labels, review history, evaluation runs, exports, and future training metadata.

### Supporting technologies

- PDF.js for PDF viewing and page navigation.
- Image viewer with zoom and pan functionality.
- Celery and Redis, or an equivalent background-job system, for long-running tasks.
- A configurable AI provider adapter for Gemini and DeepSeek.
- OCR and table preprocessing for local text-based model inference.
- Persistent filesystem or object storage for uploaded files and generated artifacts.
- A future remote GPU worker for model training.

The architecture should allow individual components to be changed without requiring a complete application rewrite.

## 4. Branding and Website Design

The website must have a modern, clean, professional, responsive design suitable for an academic research project.

Use a light background, navy or dark text, blue accents, clear typography, consistent spacing, subtle borders, rounded cards, and restrained shadows.

The interface must work well on desktop, tablet, and mobile screens.

### Top navigation

The brand and public navigation must appear on the same horizontal row.

On the far left, display:

**AutoMCS** by Puthivuth Chhoeun

The text AutoMCS must be bold and visually prominent. The phrase “by Puthivuth Chhoeun” must appear immediately beside it in a smaller, regular font.

On the same row, display:

- Home
- About
- Contact
- Login

The brand must not be placed in a separate banner above the navigation links.

After login, the application can use a separate authenticated workspace layout with a sidebar or dashboard navigation.

The website should include responsive navigation, clear active states, accessible controls, loading indicators, validation messages, empty states, and useful error messages.

## 5. Public Website Pages

The public website consists of Home, About, Contact, and Login.

### 5.1 Home

The Home page should explain the AutoMCS project and its research objectives.

Include:

- A professional hero section introducing AI-assisted decimal table extraction.
- A concise description of the problem of manual data labeling.
- Project objectives and research motivation.
- An overview of image and PDF import.
- An overview of Gemini and local DeepSeek extraction.
- A description of manual verification and correction.
- An explanation of evaluation and ground-truth dataset exports.
- A workflow illustration using synthetic or generic example data.
- Benefits such as reducing repetitive work, improving consistency, and supporting reproducible research.
- A Login button.
- A footer containing appropriate project information.

The Home page must never expose private documents, actual extracted values, private labels, AI predictions, workspace statistics, generated exports, or links to protected files.

### 5.2 About

The About page should describe:

- Project background.
- Research motivation.
- Research objectives.
- Proposed methodology.
- The researcher, Puthivuth Chhoeun.
- Academic supervisor.
- Institution or department.
- Technologies used.
- Expected research contributions.

Supervisor, institution, and other academic details must be configurable until the correct information is supplied.

### 5.3 Contact

The Contact page should include the researcher's approved contact information, institutional email if available, and an optional contact form.

The backend must validate submissions and protect the form against spam and abuse.

Do not invent contact details.

### 5.4 Login

The Login page should include:

- Username or email.
- Password.
- Password visibility toggle.
- Form validation.
- Loading and error states.
- Secure authentication.
- Redirect to the private dashboard after successful login.

Public registration should be disabled by default. New accounts should be created through an authorized administrative process unless registration is explicitly required.

## 6. Authentication and Private Workspace

After login, the user enters a private research workspace.

The workspace should include:

- Dashboard.
- Data / Projects.
- AI Prediction.
- Manual Labeling.
- Compare and Verify.
- Evaluation.
- Export Dataset.
- Training.
- Settings.
- Logout.

The AI Prediction, Manual Labeling, and Compare and Verify features can be accessible from a selected project's document workspace rather than appearing as unrelated global modules.

All private pages, APIs, original files, prediction records, labels, exports, and model-management actions must require authentication and appropriate authorization.

## 7. Dashboard

The dashboard should provide an overview of the currently selected project.

Display useful metrics such as:

- Total documents.
- Number of imported images and PDFs.
- Documents awaiting extraction.
- Documents currently processing.
- Documents awaiting review.
- Completed extraction jobs.
- Failed jobs.
- Total predicted cells.
- Corrected cells.
- Approved ground-truth cells.
- Recent project activity.

Every metric must be calculated from authorized data. AI predictions and verified ground-truth labels must be displayed separately.

The dashboard should provide shortcuts to upload documents, run extraction, review uncertain values, evaluate results, and export datasets.

## 8. Project Management

The Data page must support creating and managing multiple independent projects.

Users should be able to create, select, rename, archive, and manage projects.

Each project must maintain its own:

- Original documents.
- Extracted tables.
- AI predictions and prediction history.
- Manual labels and verified values.
- Review queue.
- Evaluation runs.
- Export jobs and files.
- Dataset versions.
- Future training jobs and model versions.
- Project settings and activity history.

Switching projects must not mix their documents, predictions, labels, or exports.

Every database query and file operation must be scoped to the project that the authenticated user is authorized to access.

## 9. Data Import: Individual Images, Image Folders, and PDFs

Data import is a core feature of AutoMCS.

The Data page must provide separate, clearly labeled options for importing images, importing an image folder, and importing PDF documents.

### 9.1 Individual image import

Allow users to select one image or multiple image files.

Support configurable image formats such as PNG, JPEG, and WebP.

Show file previews, filenames, sizes, import progress, and validation errors.

### 9.2 Image-folder import

Allow users to select an entire folder of images using the browser's directory-selection capability.

The system must:

1. Enumerate supported files in the selected folder.
2. Ignore unsupported files and clearly report which files were skipped.
3. Show the total number of supported files before processing.
4. Allow users to cancel or confirm the import.
5. Upload supported files with progress indicators.
6. Detect duplicate files where possible.
7. Preserve original filenames and optional relative subfolder information as metadata.
8. Associate every imported file with the currently selected project.
9. Allow failed files to be retried without re-uploading successful files unnecessarily.

If folder selection is unavailable in the browser, provide a fallback multi-file picker.

### 9.3 PDF import

Allow users to upload individual or multiple PDF documents.

Display page count, file size, upload status, and a PDF preview when appropriate.

The system should support page navigation and allow extraction from selected pages or the entire document when implemented.

### 9.4 Import safeguards

- Preserve original files unchanged.
- Validate actual file content, not only file extensions.
- Configure maximum file sizes and batch limits.
- Generate safe internal storage identifiers.
- Prevent unsafe filenames and path traversal.
- Provide duplicate detection and clear duplicate-handling options.
- Support cancellation, retries, and progress reporting.
- Keep all imported files in persistent storage.

## 10. AI Extraction Provider Selection

When a user starts an extraction job, AutoMCS must ask which AI provider should be used.

Provide two choices:

### Option A: Gemini API

Use a configurable, vision-capable Gemini model to process images directly and extract table structure and values.

The system should:

- Store the API key securely on the backend.
- Allow the administrator to configure the Gemini model.
- Validate that the selected model supports the required image input.
- Send only the documents or pages selected for processing.
- Handle API errors, rate limits, quota exhaustion, and network failures.
- Record the provider, model, settings, and result for each extraction attempt.
- Allow users to retry failed jobs.
- Never expose API keys in browser code or public responses.

The exact Gemini model should be configurable because available models, capabilities, and pricing may change.

### Option B: Local DeepSeek 1.5B

Use the DeepSeek-R1-Distill-Qwen-1.5B model as a locally hosted extraction assistant.

Because this model is text-oriented rather than a native vision model, the local pipeline must include OCR and table preprocessing for image-based input.

The local pipeline should:

1. Read the image or selected PDF page.
2. Detect or identify the relevant table.
3. Perform OCR to recover text and decimal values.
4. Preserve row, column, and cell-position information where possible.
5. Supply the extracted content and relevant structural information to DeepSeek.
6. Ask the model to return structured JSON conforming to the defined schema.
7. Validate the returned JSON.
8. Normalize valid decimal values.
9. Store predictions and warnings for review.

OCR and table detection should be treated as separate components so they can be improved independently.

The system must not claim that DeepSeek directly reads images unless a compatible vision-capable model or additional vision component is actually used.

### Provider selection behavior

The provider should be selected per extraction job. The application should also allow an administrator to configure a default provider.

Users should see the selected provider, model, processing status, and any configuration errors before starting a job.

The same standardized output schema must be used for both providers so that manual labeling, verification, evaluation, and export remain consistent.

## 11. Automatic Local Model Download and Loading

AutoMCS must include a model manager that automatically checks whether the local DeepSeek model is ready.

If model files are missing, the system should download them automatically when automatic downloading is enabled.

### Required workflow

1. The user selects Local DeepSeek.
2. The backend checks the configured local model runtime.
3. The model manager checks the model directory and required files.
4. If the model is already installed, reuse it.
5. If the model is missing, verify connectivity and available storage.
6. Download the model and tokenizer files from the configured trusted repository and pinned revision.
7. Display download progress and status.
8. Verify downloaded files and handle interrupted downloads.
9. Load the model into the configured runtime.
10. Run a lightweight readiness check.
11. Allow extraction only when the model is ready.
12. Show useful errors and retry options if initialization fails.

The model manager must prevent multiple simultaneous jobs from downloading the same model unnecessarily.

It should distinguish between model files being downloaded, the model being loaded, the model being ready, and a loading failure.

### Model runtime

The implementation should select a compatible local inference runtime based on the target server's operating system and hardware.

The runtime may use a local model runner or a supported Python inference framework. If a local runner already manages the model files, AutoMCS should reuse that installation instead of downloading another copy.

### Model storage

Model files must be stored in a configurable persistent model directory outside the replaceable application source directory.

For example:

/srv/automcs/models/deepseek-1.5b/

The directory should contain the required model files, tokenizer files, and a manifest recording the repository, revision, format, and installation status.

The application should never automatically delete installed model files during an ordinary deployment.

### Download and loading settings

Provide settings for:

- Automatic download enabled or disabled.
- Model repository and pinned revision.
- Model directory.
- Inference runtime.
- Download progress.
- Model readiness status.
- Retry and reload actions.
- Optional model removal through an explicit administrative action.

The system must not claim a model has been loaded or tested until the runtime confirms it.

## 12. Batch AI Prediction

AI extraction must support processing one document or many selected documents.

For each document, the system should track:

- Extraction provider.
- Model identifier and version.
- Job identifier.
- Submission and completion timestamps.
- Processing status.
- Error information.
- Prediction attempts.
- Number of cells extracted.
- Number of uncertain or malformed values.
- Review status.

Use a background-job system for long-running extraction tasks.

The interface should display progress and allow users to view job details, cancel eligible jobs, retry failures, and inspect uncertain results.

A failed document should not prevent unrelated documents in the same batch from completing.

Rerunning extraction must not silently overwrite approved ground-truth labels.

## 13. Decimal Normalization

All approved output values must follow a documented two-decimal-place policy.

Examples:

- `5` becomes `"5.00"`.
- `5.1` becomes `"5.10"`.
- `5.126` becomes `"5.13"` if ROUND_HALF_UP is the approved rule.
- A genuinely blank cell remains `null`.
- An unreadable or failed extraction remains unresolved and is flagged for review.

The rounding rule must be confirmed against the research protocol.

Use Python's `Decimal` for authoritative normalization rather than binary floating-point arithmetic.

Preserve the raw extracted string separately from the normalized value.

Store formatted output as strings when trailing zeros matter. JSON numbers and many CSV consumers may remove trailing zeros, so exports must preserve the required string representation.

Do not invent missing values or silently convert invalid strings to zero.

The system must distinguish between:

- Original source text.
- Raw AI prediction.
- Normalized prediction.
- Human-corrected value.
- Approved ground-truth value.

## 14. Table Structure and JSON Schema

AutoMCS must preserve table rows, columns, blank cells, and document references.

A representative output structure is:

{
  "document_id": "doc_001",
  "page_number": 1,
  "columns": ["I", "II", "III", "IV", "V"],
  "rows": [
    {
      "No": 1,
      "I": "13.45",
      "II": "14.56",
      "III": null,
      "IV": null,
      "V": null
    },
    {
      "No": 2,
      "I": null,
      "II": null,
      "III": null,
      "IV": null,
      "V": null
    }
  ]
}

This is an illustrative schema and must be adapted to the actual research dataset.

The internal data model should also preserve cell coordinates or other source-position information where available.

For each cell, store the raw prediction, normalized prediction, verified value, source document, page, row and column positions, review status, confidence information if supported, and relevant correction history.

## 15. Manual Labeling

Manual labeling must remain available even when AI extraction is enabled.

Users should be able to:

- Create labels manually.
- Correct AI predictions.
- Enter values when extraction fails.
- Edit individual cells.
- Navigate between cells efficiently.
- Save changes and see the save status.
- Mark records as reviewed.
- Approve verified values.
- Add correction notes or reasons.
- Review previous versions.

Every label should record its source, such as AI, manual entry, human correction, or verification.

Manual edits must not destroy the original prediction history.

The application must distinguish between unreviewed, corrected, and approved values.

## 16. Compare and Verify Interface

Provide a dedicated comparison workspace showing the original document and its structured extracted table side by side.

The original document viewer should support:

- PDF page navigation.
- Image zoom and pan.
- Page and document navigation.
- Source inspection.

The extracted table editor should support:

- Editable cells.
- Row and column navigation.
- Keyboard shortcuts where appropriate.
- Missing-value indicators.
- Uncertain-value warnings.
- Malformed-value warnings.
- Mismatch highlighting.
- Approve, reject, and correct actions.
- Notes and correction reasons.
- Previous and next record navigation.
- Save status and error handling.
- Version history or undo where supported.

Where source coordinates are available, selecting a cell should help the user locate the corresponding region in the original document.

Original files and original prediction attempts should remain immutable. Human corrections must be recorded separately.

## 17. Review Queue

Provide a review queue containing records that require human attention.

Examples include:

- Missing values.
- Low-confidence predictions, where confidence is available.
- Invalid JSON output.
- Invalid decimal strings.
- Table structure mismatches.
- OCR failures.
- Extraction errors.
- Values changed by normalization.
- Records awaiting approval.

Users should be able to filter by project, document, provider, status, and error type.

Approved records should leave the pending-review queue unless they are explicitly reopened.

## 18. Evaluation

The Evaluation page must measure extraction quality against verified ground-truth labels.

Possible metrics include:

- Exact cell match accuracy.
- Table-level accuracy.
- Document-level accuracy.
- Mean absolute error for valid numerical values.
- Missing prediction counts.
- Extra prediction counts.
- Invalid or malformed value counts.
- Uncertain prediction counts.
- Mismatch counts by document or column.

The system must explicitly define how blank cells, invalid values, missing predictions, and numerical tolerances are handled.

Users should be able to compare different extraction providers or model versions on the same verified dataset.

Evaluation results must identify the dataset version, model, provider, configuration, and evaluation rules used.

Unreviewed predictions must never be presented as ground truth.

For model comparisons, the system should support a held-out test set to avoid evaluating models only on data used for development or training.

## 19. Dataset Export

Provide a private Export Dataset page.

The default export must include approved or verified labels and the corresponding original documents.

Users should be able to select the project, documents, or approved records to export.

The export should support:

- JSON.
- CSV.
- Optional JSONL.
- Original image and PDF files.
- Optional metadata.
- Optional correction history.
- A ZIP archive containing the selected files.

Example structure:

Dataset/
  image_pdf/
    original_file_001.pdf
    original_file_002.png
  groundtruth/
    original_file_001.json
    original_file_001.csv
    original_file_002.json
    original_file_002.csv

The export process must match each label to the correct original file and preserve the required table structure and decimal formatting.

Display export progress, errors, completion status, and authorized download links.

Use safe filenames and prevent unauthorized access to export files.

## 20. Future Model Training

Include a Training page in the application architecture.

Initially, the page may display a clear Coming Later status until training infrastructure is configured.

Do not pretend that training is running when it is not.

When enabled, training should support:

1. Selecting an approved dataset.
2. Creating a versioned dataset snapshot.
3. Defining training, validation, and test splits.
4. Selecting a supported model and training framework.
5. Configuring hyperparameters and random seeds.
6. Submitting background jobs to a GPU server.
7. Tracking progress, logs, errors, and resource use.
8. Saving checkpoints and training artifacts.
9. Recording configuration and dataset lineage.
10. Evaluating the resulting model on a held-out dataset.
11. Comparing model versions.
12. Promoting a model only after explicit user approval.

Training jobs should run through a background worker or remote training service rather than blocking the main web application.

The architecture must support adding a higher-performance server later without redesigning the entire application.

## 21. Database Design

Use PostgreSQL with relationships that support project isolation and traceability.

Suggested entities include:

- Users and authentication records.
- Projects.
- Documents and storage references.
- Tables, rows, and cells.
- Extraction jobs.
- Prediction attempts.
- Labels and verified values.
- Review records.
- Audit logs.
- Evaluation runs.
- Export jobs and artifacts.
- Model installations and configurations.
- Dataset versions.
- Training runs.
- Model versions and evaluation metrics.

Store large original files and model checkpoints in persistent file or object storage, rather than placing the file contents directly into ordinary database records unless a specific requirement justifies it.

The database should retain the metadata and storage references needed to retrieve each file securely.

## 22. Proposed API Endpoints

Example Django REST Framework endpoints:

Authentication:

- POST `/api/auth/login/`
- POST `/api/auth/logout/`
- GET `/api/auth/me/`

Projects:

- GET and POST `/api/projects/`
- GET, PATCH, and DELETE `/api/projects/{id}/`

Documents:

- GET and POST `/api/projects/{id}/documents/`
- GET `/api/documents/{id}/`

Extraction:

- POST `/api/documents/{id}/extract/`
- GET `/api/jobs/{id}/`
- POST `/api/jobs/{id}/retry/`
- GET `/api/documents/{id}/predictions/`

Labeling and review:

- PATCH `/api/cells/{id}/label/`
- POST `/api/predictions/{id}/review/`
- GET `/api/cells/{id}/history/`

Evaluation:

- POST `/api/projects/{id}/evaluations/`
- GET `/api/evaluations/{id}/`

Exports:

- POST `/api/projects/{id}/exports/`
- GET `/api/exports/{id}/`
- GET `/api/exports/{id}/download/`

Model management:

- GET `/api/models/local/status/`
- POST `/api/models/local/download/`
- POST `/api/models/local/load/`

Future training:

- POST `/api/projects/{id}/training-runs/`
- GET `/api/training-runs/{id}/`

These are proposed endpoints. The implementation may adjust them while preserving the specified functionality.

Every private endpoint must authenticate the user and verify access to the relevant project and resource.

## 23. Persistent Storage and Deployment

A critical requirement is that updating, replacing, or deleting the website source code must not delete valuable research data.

Separate replaceable application code from persistent data.

Example deployment structure:

/opt/automcs/
  releases/
    current/                 # Replaceable application source

/srv/automcs/
  data/
    originals/               # Uploaded documents
    exports/                 # Generated datasets
    temporary/               # Temporary processing data
  models/
    deepseek-1.5b/            # Persistent local model
  backups/                   # Managed backup files

PostgreSQL must use a persistent database volume or a managed database service.

The actual paths should be configurable for Windows development and Linux production.

Deployment requirements:

- Do not store irreplaceable uploads only inside the application source directory.
- Do not delete persistent directories during normal deployments.
- Keep API keys and passwords outside source control.
- Use environment variables or a secret manager.
- Apply database migrations safely.
- Back up PostgreSQL and original files.
- Test restoring backups.
- Document upgrade and rollback procedures.
- Avoid destructive deployment scripts.
- Keep model files across application upgrades.

## 24. Security and Privacy

Security is essential because AutoMCS stores research documents and ground-truth datasets.

Required controls include:

- Authentication on all private pages and APIs.
- Backend authorization for every project, document, cell, job, and export.
- Secure password hashing.
- Secure session or token handling.
- CSRF protection where applicable.
- HTTPS in production.
- Server-side storage of Gemini API keys.
- File validation and upload limits.
- Safe file naming and storage.
- Protection against path traversal.
- Rate limiting and request validation.
- Controlled access to original files and exports.
- Audit logs for important actions.
- Appropriate backup access controls.
- A documented retention policy.

The public website must use only synthetic or generic examples and must never reveal private workspace content.

## 25. End-to-End Workflow

The intended workflow is:

1. A visitor views Home, About, or Contact.
2. The researcher logs in.
3. The researcher creates or selects a project.
4. The researcher imports individual images, multiple images, a folder of images, or PDFs.
5. The researcher selects documents for extraction.
6. The researcher chooses Gemini API or Local DeepSeek 1.5B.
7. AutoMCS checks the provider configuration and model readiness.
8. If the local model is missing, AutoMCS downloads and validates it when automatic download is enabled.
9. The extraction job processes the selected documents.
10. AutoMCS saves structured predictions, raw values, normalized values, and warnings.
11. The researcher compares predictions with the original documents.
12. The researcher corrects and approves labels.
13. The researcher evaluates extraction quality using verified ground truth.
14. The researcher exports approved labels and corresponding originals.
15. In the future, the researcher can use versioned approved datasets for model training on a GPU server.

## 26. Implementation Phases

### Phase 1: Foundation

Set up Next.js, Django REST Framework, PostgreSQL, authentication, projects, persistent storage, and the main application structure.

### Phase 2: Public Website and Workspace

Implement Home, About, Contact, Login, Dashboard, project management, navigation, and responsive styling.

### Phase 3: Document Import

Implement individual image uploads, multi-image uploads, folder import, PDF upload, previews, validation, progress indicators, and duplicate handling.

### Phase 4: AI Provider Integration

Implement the Gemini API provider, local DeepSeek provider, OCR preprocessing, model manager, automatic model downloads, model loading, and extraction-job management.

### Phase 5: Labeling and Verification

Implement editable tables, manual labels, comparison views, review queues, approval workflows, and correction history.

### Phase 6: Evaluation and Export

Implement metrics, verified-ground-truth selection, JSON/CSV/ZIP exports, and authorized downloads.

### Phase 7: Production Hardening

Implement authorization tests, persistent deployment, database migrations, backups, recovery testing, monitoring, and security checks.

### Phase 8: Future Model Training

Implement dataset versioning, GPU-worker integration, training jobs, logs, model checkpoints, evaluation, and model version management.

## 27. Acceptance Criteria

The initial release is acceptable when:

1. The branding and public navigation appear on the same row.
2. Public pages do not expose private data.
3. Authorized users can create and switch between isolated projects.
4. Users can import individual images, multiple images, image folders, and PDFs.
5. Folder import reports unsupported or failed files.
6. Users can select Gemini or local DeepSeek for an extraction job.
7. The Gemini provider handles configuration errors and API failures.
8. The local model manager detects missing files and downloads the configured model when enabled.
9. Model readiness is verified before local extraction begins.
10. Local inference uses a compatible OCR and table-preprocessing pipeline for image input.
11. Batch extraction preserves table rows, columns, and blank cells.
12. Decimal normalization follows the documented two-decimal rule.
13. Original values, predictions, and approved labels remain separate.
14. Rerunning extraction does not silently overwrite approved labels.
15. Manual corrections and approvals are traceable.
16. Evaluation uses verified labels and documented rules.
17. Exports contain the correct originals and corresponding approved labels.
18. Future training is clearly marked as unavailable until implemented.
19. Uploaded files, model files, and database records survive application redeployment.
20. Backup restoration and project-isolation tests pass.

## 28. Decisions to Finalize

Before production deployment, confirm:

- Supervisor and institution details.
- Whether the application will support one researcher or multiple authorized users.
- The exact table schema and expected JSON output.
- The official rounding rule.
- Supported file formats, file-size limits, and batch limits.
- The Gemini model to use.
- The local DeepSeek inference runtime and quantization format, if applicable.
- The OCR engine and table-detection method.
- The operating system and hardware for local inference.
- The production server and storage locations.
- The future GPU server and training framework.
- Backup frequency, retention, and recovery requirements.

## Final Project Definition

AutoMCS is a project-based research web application for importing images and PDFs, automatically extracting decimal tables using a selectable Gemini API or local DeepSeek 1.5B pipeline, correcting and verifying predictions, evaluating extraction quality, and exporting reliable ground-truth datasets.

The system must include an automatic local-model download and loading manager, preserve original table structure and two-decimal formatting, enforce strict project-level access control, and store all research data and model artifacts persistently outside the replaceable application source directory.

The implementation should prioritize reliable extraction, human verification, data integrity, reproducibility, and secure deployment before activating advanced model-training capabilities.

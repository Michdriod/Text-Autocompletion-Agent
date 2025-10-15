# Text Autocompletion Agent - Multi-Mode AI Assistant

## Overview

A comprehensive AI-powered text processing system built with FastAPI and Groq LLMs. This application provides six specialized modes for text generation, enrichment, summarization, and document creation. Features include intelligent document summarization with Google Drive integration, adaptive token management, and zero-truncation guarantees for large summaries.

## Features

### Core Capabilities

- **Six Specialized AI Modes:**
  1. **Context-Aware Completion**: Enhances and continues long-form text while preserving style and context
  2. **Structured Context Enrichment**: Expands content based on topic and context parameters
  3. **Input Refinement**: Polishes and clarifies messy or incomplete text
  4. **Payload Description Agent**: Converts structured JSON data into natural language descriptions
  5. **Intelligent Document Summarization**: Advanced summarization with adaptive strategies and zero truncation
  6. **Document Generation**: Creates comprehensive documents from high-level context and descriptions

### Advanced Features

- **Intelligent Document Summarization (Mode 5)**
  - Adaptive summarization strategies based on document size
  - Dynamic token allocation (2.2x-3.0x multipliers)
  - Zero-truncation guarantee with automatic sentence completion
  - Custom user prompts with target word extraction
  - Supports multiple input sources: file upload, Google Drive, raw text
  - Output formats: Markdown, Plain Text, or Both

- **Google Drive Integration**
  - Direct URL input for public Google Drive files
  - Automatic file type detection (Google Docs, Sheets, Slides, PDFs)
  - Smart export handling (Docs→DOCX, Sheets→XLSX, Slides→PDF)
  - File size validation (10MB limit)
  - Supports both uploaded files and Google Workspace documents

- **On-Demand Generation**
  - Fresh suggestions generated for each request
  - No persistent storage of suggestions
  - Dynamic response generation
  - Real-time processing feedback

- **Intelligent Processing**
  - Context preservation across generations
  - Adaptive tone and style matching
  - Structured data interpretation
  - Multi-stage summarization pipeline
  - Automatic chunking for large documents

- **Dynamic Parameters**
  - Mode-specific minimum word requirements
  - Configurable output length (words/characters)
  - Target word count with intelligent enforcement
  - Adjustable generation parameters per mode
  - Custom user prompts for Mode 5

### User Interface

- Modern, responsive web interface
- Real-time validation and feedback
- Adaptive input forms based on mode
- Clear mode descriptions and instructions
- Mobile-friendly design

## Project Structure

```plaintext
Text-Autocompletion-Agent/
├── config/
│   ├── __init__.py
│   └── settings.py             # Application configuration and constants
├── handlers/
│   ├── autocomplete.py         # FastAPI router for enrichment endpoints
│   ├── summarize_document.py  # Mode 5 document summarization endpoint
│   └── document_generation.py # Mode 6 document generation endpoint
├── logic/
│   ├── mode_1.py               # Context-Aware Completion logic
│   ├── mode_2.py               # Structured Context Enrichment logic
│   ├── mode_3.py               # Input Refinement logic
│   ├── mode_4.py               # Payload Description Agent logic
│   ├── mode_5.py               # Intelligent Document Summarization pipeline
│   └── mode_6.py               # Document Generation logic
├── services/
│   ├── ingestion.py            # Document text extraction (PDF, DOCX, TXT, XLSX)
│   ├── preprocess.py           # Text cleaning and normalization
│   ├── baseline.py             # Document metrics computation
│   ├── chunking.py             # Smart document chunking for large files
│   ├── summarizer.py           # Per-chunk summarization
│   ├── merge.py                # Partial summary merging
│   ├── refinement.py           # Summary refinement planning
│   ├── finalize.py             # Final summary polishing
│   ├── formatter.py            # Output formatting (Markdown/Plain)
│   └── models.py               # Data models and schemas
├── utils/
│   ├── generator.py            # LLM API integration (Groq)
│   ├── validator.py            # Input validation and token calculation
│   ├── google_drive.py         # Google Drive public file downloader
│   └── __init__.py
├── tests/
│   ├── test_*.py               # Comprehensive test suite
│   └── conftest.py             # Test fixtures and configuration
├── main.py                     # FastAPI application entry point
├── index.html                  # Modern responsive web UI
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not committed)
├── README.md                   # This file
├── IMPLEMENTATION_COMPLETE.md  # Implementation summary
└── MODE5_INTELLIGENT_SUMMARIZATION.md  # Technical documentation
```

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd Text-Autocompletion-Agent
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv textautocom
   source textautocom/bin/activate  # On Windows: textautocom\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:

   ```plaintext
   GROQ_API_KEY=your_api_key_here
   ```

## Configuration

1. **Environment Variables** (`.env` file)
   - `GROQ_API_KEY`: Your Groq API key (required for Mode 5, 6)
   - `GROQ_API_KEY`: Your Groq API key (required for Modes 1-4)

2. **Application Settings** (in `config/settings.py`)
   - `MAX_FILE_SIZE`: Maximum upload size (default: 10MB)
   - `MAX_PROMPT_LENGTH`: Max custom prompt length (default: 2000 chars)
   - `SUPPORTED_FORMATS`: Document formats (PDF, DOCX, TXT, XLSX)

3. **Model Parameters** (in `utils/generator.py`)
   - Temperature settings per mode (0.2-0.7)
   - Token limits and generation parameters
   - Model selection: Groq LLaMA
   - Adaptive token budgets for summarization

## Running the App

1. Start the FastAPI server:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. Access the web interface:
   - Open `index.html` in a browser
   - Or visit `http://localhost:8000` for the API
   - Python -m http.server 8002

## API Endpoints

### `POST /autocomplete`

Main endpoint for text enrichment and generation (Modes 1-4).

**Request Body:**

```json
{
  "mode": "mode_1|mode_2|mode_3|mode_4",
  "text": "string",
  "header": "string",
  "body": {},
  "min_input_words": 0,
  "max_output_length": {
    "type": "words|characters",
    "value": 0
  }
}
```

**Response:**

```json
{
  "completion": "string",
  "mode": "string"
}
```

### `POST /summarize-document`

Advanced document summarization endpoint (Mode 5).

**Request Body (multipart/form-data):**

```
file: File (optional) - PDF, DOCX, TXT, or XLSX file
google_drive_url: string (optional) - Public Google Drive URL
raw_text: string (optional) - Direct text input
target_words: integer (optional) - Desired summary length
output_format: string (optional) - "markdown", "plain", or "both"
user_prompt: string (optional) - Custom summarization instructions
```

**Response:**

```json
{
  "markdown_summary": "string",
  "plain_summary": "string (if requested)",
  "meta": {
    "source_words": 15420,
    "target_words": 2000,
    "actual_words": 1980,
    "summarization_strategy": "chunked",
    "length_enforcement": {
      "truncated": false,
      "complete_sentences": true,
      "within_target": true
    }
  }
}
```

### `POST /generate-document`

Document generation from context (Mode 6).

**Request Body:**

```json
{
  "header": "High-level context",
  "body": "Detailed description",
  "output_format": "markdown|plain|both"
}
```

**Response:**

```json
{
  "markdown_document": "string",
  "plain_document": "string (optional)",
  "meta": {
    "word_count": 1250,
    "generation_strategy": "structured"
  }
}
```

### `GET /health`

Returns API health status and supported features.

**Response:**

```json
{
  "status": "healthy",
  "modes": ["mode_1", "mode_2", "mode_3", "mode_4", "mode_5", "mode_6"],
  "features": ["google_drive", "custom_prompts", "multi_format"]
}
```

## Processing Modes Explained

### Mode 1: Context-Aware Completion

**Purpose:** Enhance and continue long-form text while preserving style and context.

**How It Works:**
1. Analyzes input text for style, tone, and context
2. Generates continuation that matches the original voice
3. Maintains narrative flow and thematic consistency

**Input Requirements:**
- Text: Minimum 20 words
- Optional: Max output length (words/characters)

**Use Cases:**
- Blog post continuation
- Article enhancement
- Creative writing assistance
- Story development

**Technical Details:**
- Uses Groq LLaMA 3.1 70B
- Temperature: 0.7 (creative)
- Adaptive token budgets

### Mode 2: Structured Context Enrichment

**Purpose:** Generate comprehensive content from topic and context parameters.

**How It Works:**
1. Takes high-level topic (header) and detailed context (text)
2. Expands and enriches the content
3. Maintains structured, coherent output

**Input Requirements:**
- Header: Topic or theme
- Text: Supporting context
- Min Words: 2 combined

**Use Cases:**
- Topic expansion
- Educational content development
- Research summaries
- Technical explanations

**Technical Details:**
- Uses Groq LLaMA 3.1 70B
- Temperature: 0.6
- Structured generation

### Mode 3: Input Refinement

**Purpose:** Clean, polish, and clarify messy or incomplete text.

**How It Works:**
1. Analyzes input for grammar, structure, and clarity issues
2. Rewrites with improved structure and precision
3. Preserves original meaning and intent

**Input Requirements:**
- Text: Any length (no minimum)
- Flexible input (notes, drafts, rough text)

**Use Cases:**
- Note cleanup
- Grammar correction
- Email polishing
- Draft refinement

**Technical Details:**
- Uses Groq LLaMA 3.1 70B
- Temperature: 0.3 (precise)
- Focus on clarity

### Mode 4: Payload Description Agent

**Purpose:** Convert structured JSON data into natural language descriptions.

**How It Works:**
1. Parses JSON payload structure
2. Interprets data relationships and values
3. Generates human-readable descriptions

**Input Requirements:**
- Header: Context or purpose
- Body: Valid JSON object
- Min Words: 2 combined

**Use Cases:**
- API response descriptions
- Data report generation
- Configuration summaries
- Log interpretation

**Technical Details:**
- Uses Groq LLaMA 3.1 70B
- Temperature: 0.4
- Structured interpretation

### Mode 5: Intelligent Document Summarization

**Purpose:** Generate intelligent, comprehensive summaries with zero truncation.

**How It Works:**

**Pipeline Architecture:**

1. **Ingestion Stage** (`services/ingestion.py`)
   - Extracts text from PDF, DOCX, TXT, XLSX files
   - Handles Google Drive URLs with automatic export
   - Processes raw text input
   - Returns clean text + metadata

2. **Preprocessing Stage** (`services/preprocess.py`)
   - Cleans extracted text (removes artifacts, normalizes whitespace)
   - Prepares text for analysis
   - Maintains readability

3. **Baseline Analysis** (`services/baseline.py`)
   - Computes document metrics (word count, complexity)
   - Determines processing strategy
   - Sets target parameters

4. **Strategy Selection** (`logic/mode_5.py`)
   - **Small documents (≤500 words)**: Direct summarization
   - **Large documents (>500 words)**: Chunked summarization

5. **Direct Summarization Path** (for small documents)
   - Uses `_build_system_prompt()` for intelligent instructions
   - Adaptive token budgets (2.2x-3.0x multipliers)
   - Single-pass generation with Groq/llama
   - Zero truncation guarantee

6. **Chunked Summarization Path** (for large documents)
   - **Chunking** (`services/chunking.py`): Splits into logical segments
   - **Per-Chunk Summarization** (`services/summarizer.py`): Summarizes each chunk
   - **Merging** (`services/merge.py`): Combines partial summaries
   - **Final Synthesis**: Creates unified, coherent summary

7. **Finalization** (`services/finalize.py`)
   - Ensures completeness (no truncation)
   - Validates target word count
   - Polishes final output

8. **Formatting** (`services/formatter.py`)
   - Outputs in Markdown, Plain Text, or Both
   - Maintains structure and readability

**Input Sources:**
- **File Upload**: PDF, DOCX, TXT, XLSX (max 10MB)
- **Google Drive URL**: Public links (Docs, Sheets, Slides, Files)
- **Raw Text**: Direct paste

**Input Parameters:**
- `target_words`: Desired summary length (optional)
  - Small docs (≤500 words): Default 100 words
  - Large docs (>500 words): Default 20% of original
- `user_prompt`: Custom instructions (optional, max 2000 chars)
  - Can include target: "summarize in 150 words"
  - Overrides parameter target if specified
- `output_format`: "markdown", "plain", or "both"

**Key Features:**
- **Intelligent Prompts**: Adapts strategy based on target size
- **Dynamic Token Budgets**:
  - Small (≤500 words): 2.2x multiplier
  - Medium (501-1500 words): 2.5x multiplier
  - Large (>1500 words): 3.0x multiplier
- **Zero Truncation**: Automatic sentence completion
- **Target Precedence**: prompt > parameter > defaults
- **Quality Metrics**: Tracks truncation, completeness, accuracy

**Use Cases:**
- Academic paper summarization
- Report condensation
- Meeting notes summaries
- Long-form content digestion

**Technical Details:**
- Groq/llama
- Temperature: 0.3 (balanced)
- Max tokens: 8,000 (adaptive)
- Multi-stage pipeline with quality checks

### Mode 6: Document Generation

**Purpose:** Create comprehensive documents from high-level context and detailed descriptions.

**How It Works:**
1. Takes high-level context (header) and detailed description (body)
2. Generates structured, professional documents
3. Maintains logical flow and coherence

**Input Requirements:**
- Header: High-level context or purpose
- Body: Detailed description or requirements
- Min Words: 2 combined

**Use Cases:**
- Technical documentation
- Business proposals
- Project specifications
- Report generation

**Technical Details:**
- Groq/llama
- Temperature: 0.4
- Structured generation with sections

## Frontend Usage

### Accessing the Application

1. Start the backend server (see Usage section)
2. Open browser to `http://localhost:8000`
3. Interface loads with mode selector

### Mode-Specific Usage

#### Mode 1-4: Text Enrichment
1. Select mode from dropdown (Mode 1, 2, 3, or 4)
2. Set parameters:
   - **Min Words**: Minimum output length
   - **Max Words**: Maximum output length (optional)
   - **Temperature**: Creativity level (0.0-1.0)
3. Paste or type input text in textarea
4. Click "Process" button
5. View enriched output below

**Example Mode Settings:**
- **Mode 1** (Basic): min=20, max=50, temp=0.5
- **Mode 2** (Creative): min=30, max=100, temp=0.8
- **Mode 3** (Context): min=25, max=75, temp=0.6
- **Mode 4** (Advanced): min=40, max=150, temp=0.7

#### Mode 5: Document Summarization
1. Select "Mode 5 (Summarization)" from dropdown
2. **Choose Input Method** (radio buttons):
   - **Upload File**: Click "Choose File" → Select PDF/DOCX/TXT/XLSX
   - **Google Drive URL**: Paste public Google Drive link
   - **Paste Text**: Type or paste document content directly

3. **Configure Summary Settings**:
   - **Custom Prompt** (optional): Add instructions like:
     - "Summarize in 200 words"
     - "Focus on key findings"
     - "Highlight main arguments in 150 words"
   - **Target Words** (optional): Specify numeric target
     - Overridden if prompt contains target
     - Defaults to 100 words (small docs) or 20% (large docs)
   - **Output Format**: Select Markdown, Plain Text, or Both

4. Click "Summarize Document"
5. View summary with metadata:
   - Word count
   - Character count
   - Truncation status
   - Processing time

**Google Drive URL Examples:**
```
https://drive.google.com/file/d/1abc...xyz/view
https://docs.google.com/document/d/1abc...xyz/edit
https://docs.google.com/spreadsheets/d/1abc...xyz/edit
```

**Prompt Examples:**
- "Summarize the main findings in 150 words"
- "Create an executive summary (200 words max)"
- "Give me a concise 100-word overview"
- "Summarize key points" (uses default 100 words)

#### Mode 6: Intelligent Document Generation
1. Select "Mode 6 (Generation)" from dropdown
2. **Input Requirements**:
   - **Topic/Subject**: What to write about
   - **Instructions**: Specific requirements, format, tone
   - **Target Length**: Desired word count
3. Click "Generate Document"
4. Receive intelligently generated document

### Real-Time Feedback

- **Character Counter**: Shows remaining characters for custom prompts (max 2000)
- **Progress Indicators**: Processing status during API calls
- **Error Messages**: Clear validation feedback
- **Success Indicators**: Confirmation when complete

### Tips for Best Results

**Text Enrichment (Modes 1-4):**
- Start with 2-3 sentences minimum
- Clear, grammatically correct input
- Appropriate min/max word ranges
- Lower temperature = more focused, higher = more creative

**Summarization (Mode 5):**
- For long documents (>2000 words), be specific with target
- Custom prompts override target_words parameter
- Google Drive files must be publicly accessible
- Larger targets (500+) may take 10-20 seconds
- Markdown format preserves document structure

**Document Generation (Mode 6):**
- Be specific with instructions
- Provide context and requirements
- Realistic length targets
- Clear tone/style guidance

## System Architecture & Logic

### Request Flow

```
User Request → FastAPI Router → Validation → Mode Logic → LLM API → Response Processing → User
```

### Mode 5 Detailed Pipeline (Example)

```
1. File Upload/URL/Text Input
   ↓
2. Ingestion Service (text extraction)
   ↓
3. Preprocessing (cleaning)
   ↓
4. Baseline Analysis (metrics)
   ↓
5. Strategy Selection
   ├─→ Small Doc: Direct Summarization
   │   ├─→ Build Intelligent Prompt
   │   ├─→ Calculate Token Budget (2.2x-3.0x)
   │   ├─→ Groq API Call
   │   └─→ Truncation Check & Cleanup
   │
   └─→ Large Doc: Chunked Summarization
       ├─→ Chunk Document
       ├─→ Summarize Each Chunk
       ├─→ Merge Partial Summaries
       ├─→ Final Synthesis
       └─→ Truncation Check & Cleanup
   ↓
6. Finalization (quality checks)
   ↓
7. Format Output (Markdown/Plain)
   ↓
8. Return with Metadata
```

### Key Components

#### 1. **Validation Layer** (`utils/validator.py`)
- Input validation per mode
- Token budget calculation
- Truncation detection
- Word/character counting
- Format validation

**Token Calculation Formula:**
```python
base_tokens = (target_words / 0.75) * 1.3  # 30% buffer
final_tokens = base_tokens * multiplier    # 2.2x-3.0x based on size
final_tokens = min(final_tokens, 8000)    # Groq/llamas limit
```

#### 2. **LLM Integration** (`utils/generator.py`)
- Groq/llama for summarization (Modes 5, 6)
- Groq LLaMA 3.1 70B for enrichment (Modes 1-4)
- Adaptive temperature per mode
- Token management
- Error handling and retries

#### 3. **Google Drive Handler** (`utils/google_drive.py`)
- URL parsing (extracts file ID)
- File type detection (Docs/Sheets/Slides/Files)
- Public file download via gdown library
- Automatic format conversion:
  - Google Docs → DOCX
  - Google Sheets → XLSX  
  - Google Slides → PDF
- File validation and size checks

#### 4. **Document Processing Services** (`services/`)
- **Ingestion**: Multi-format text extraction
- **Preprocessing**: Text cleaning and normalization
- **Chunking**: Intelligent document segmentation
- **Baseline**: Metrics and strategy determination
- **Summarizer**: Per-chunk and final summarization
- **Merge**: Combines partial summaries coherently
- **Finalization**: Quality assurance and polishing
- **Formatter**: Output formatting (Markdown/Plain)

### Intelligent Features

#### Adaptive Token Budgets (Mode 5)

The system dynamically allocates tokens based on summary size to prevent truncation:

| Target Words | Multiplier | Example Tokens | Can Output |
|-------------|-----------|---------------|-----------|
| ≤500        | 2.2x      | 1,155         | ~850 words |
| 501-1500    | 2.5x      | 2,165         | ~1,600 words |
| >1500       | 3.0x      | 5,200+        | ~3,900 words |

**Why This Works:**
- LLMs tokenize at ~0.75 words/token
- Base calculation: `words / 0.75 = tokens needed`
- Add 30% buffer for safety
- Apply size-based multiplier
- Result: Zero truncation, complete sentences

#### Target Word Precedence (Mode 5)

```
User Prompt Target (e.g., "in 150 words")
    ↓ overrides
Parameter Target (e.g., target_words=200)
    ↓ overrides
Default Target (100 for small, 20% for large)
```

#### Truncation Prevention

1. **Generous Token Budgets**: 2.2x-3.0x multipliers
2. **Intelligent Prompts**: Instructs model to complete sentences
3. **Automatic Detection**: `is_summary_truncated()` checks endings
4. **Cleanup**: `complete_truncated_summary()` removes incomplete sentences
5. **Validation**: Metadata tracks truncation status

### Error Handling

- **Input Validation**: Early rejection of invalid inputs
- **File Size Limits**: 10MB maximum
- **Format Validation**: Only supported file types
- **API Errors**: Graceful handling with user-friendly messages
- **Truncation Recovery**: Automatic cleanup
- **Google Drive Errors**: Specific guidance (permissions, sharing)

### Performance Optimizations

- **Single-Pass Summarization**: No refinement needed (saves API calls)
- **Smart Chunking**: Only when necessary (>500 words)
- **Parallel Processing**: Where applicable
- **Efficient Token Use**: Adaptive budgets prevent waste
- **Caching**: Document metrics cached during processing

## Extending the System

### Adding New Modes

1. **Create Logic File** in `logic/`
   ```python
   # logic/mode_7.py
   async def process(input_data):
       # Your logic here
       return result
   ```

2. **Create Handler** in `handlers/`
   ```python
   # handlers/mode_7.py
   @router.post("/mode-7")
   async def mode_7_endpoint(request: ModeRequest):
       return await Mode7().process(request)
   ```

3. **Update Validation** in `utils/validator.py`
   ```python
   def get_default_min_words(mode: ModeType) -> int:
       defaults = {
           # ... existing modes
           ModeType.mode_7: 10,
       }
   ```

4. **Add UI Elements** in `index.html`
   - Add mode option to dropdown
   - Create input form section
   - Add mode description

5. **Register in `main.py`**
   ```python
   from handlers.mode_7 import router as mode_7_router
   app.include_router(mode_7_router)
   ```

### Customizing Generation

**Adjust Model Parameters:**
```python
# utils/generator.py
temperature_map = {
    "mode_5": 0.3,  # Focused summarization
    "mode_1": 0.7,  # Creative completion
    "mode_7": 0.5,  # Your custom mode
}
```

**Modify Token Budgets:**
```python
# utils/validator.py
def calculate_max_tokens(max_output_length):
    # Adjust multipliers, buffers, limits
    pass
```

**Change System Prompts:**
```python
# logic/mode_5.py
def _build_system_prompt(self, target_words, output_format):
    # Customize instructions per mode
    pass
```

### Adding Document Formats

1. **Update Ingestion Service:**
   ```python
   # services/ingestion.py
   def extract_text(file_path: str):
       # Add new format handler
       if file_path.endswith('.rtf'):
           return extract_rtf(file_path)
   ```

2. **Update Configuration:**
   ```python
   # config/settings.py
   SUPPORTED_FORMATS = ['.pdf', '.docx', '.txt', '.xlsx', '.rtf']
   ```

3. **Update Validation:**
   ```python
   # handlers/summarize_document.py
   # Add format validation
   ```

## Testing

### Running Tests

The project includes comprehensive test suites for all major components:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_mode5_intelligent.py

# Run with coverage
pytest --cov=services --cov=logic --cov=utils

# Run with verbose output
pytest -v
```

### Test Files

#### Core Component Tests
- **`test_ingestion.py`**: Document text extraction (PDF, DOCX, TXT, XLSX)
- **`test_preprocess.py`**: Text cleaning and normalization
- **`test_chunking.py`**: Document segmentation algorithms
- **`test_baseline.py`**: Metrics calculation and strategy selection
- **`test_merge.py`**: Partial summary merging
- **`test_refinement.py`**: Quality assurance and polishing

#### Mode-Specific Tests
- **`test_mode5_intelligent.py`**: Full Mode 5 pipeline testing
  - Small document direct summarization
  - Large document chunked summarization
  - User prompt with target word extraction
  - Google Drive integration
  - Truncation prevention
  - Metadata validation

- **`test_new_summarization.py`**: Advanced summarization scenarios
  - Multi-format document handling
  - Edge cases (very small/large documents)
  - Custom output formats

- **`test_comprehensive.py`**: End-to-end integration tests
  - Full pipeline from input to output
  - Error handling scenarios
  - Performance benchmarks

#### Utility Tests
- **`test_truncation_fix.py`**: Token budget and truncation detection
  - Dynamic multiplier calculations
  - Sentence completion validation
  - Token limit enforcement

### Test Coverage

Current coverage (as of last run):
- **Ingestion Service**: 95%
- **Preprocessing**: 92%
- **Chunking**: 88%
- **Baseline Analysis**: 90%
- **Mode 5 Logic**: 87%
- **Validation Utils**: 94%

### Manual Testing

#### Backend API Testing (Swagger UI)

1. Start server: `python main.py`
2. Open: `http://localhost:8000/docs`
3. Test endpoints:
   - **POST /autocomplete**: Test Modes 1-4
   - **POST /summarize-document**: Test Mode 5 with files/URLs/text
   - **POST /generate-document**: Test Mode 6
   - **GET /health**: Verify server status

#### Frontend Testing

1. Open `http://localhost:8000` in browser
2. **Mode 1-4 Tests**:
   - Enter sample text (2-3 sentences)
   - Set min/max words, temperature
   - Verify output length and quality

3. **Mode 5 Tests**:
   - **File Upload**: Upload PDF/DOCX sample
   - **Google Drive**: Test public Google Doc/Sheet URL
   - **Paste Text**: Copy long article (500+ words)
   - **Custom Prompt**: "Summarize in 150 words"
   - **Verify**: Output length, no truncation, metadata accurate

4. **Mode 6 Tests**:
   - Topic: "Climate Change"
   - Instructions: "Write a 300-word informative article"
   - Verify: Generated document meets requirements

### Sample Test Data

Create `test_data/` directory with sample files:
- `small_doc.txt` (100-300 words)
- `medium_doc.pdf` (500-1000 words)
- `large_doc.docx` (2000-3000 words)
- `spreadsheet.xlsx` (with text in cells)

### Google Drive Test URLs

For testing Google Drive integration (must be publicly accessible):
```
# Google Doc
https://docs.google.com/document/d/YOUR_DOC_ID/edit?usp=sharing

# Google Sheet
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit?usp=sharing

# Direct file link
https://drive.google.com/file/d/YOUR_FILE_ID/view?usp=sharing
```

**Setting Public Access:**
1. Open file in Google Drive
2. Click "Share" button
3. Change "Restricted" to "Anyone with the link"
4. Copy link

### Known Test Issues

- **Rate Limits**: Anthropic/Groq APIs have rate limits; space out test runs
- **Network Dependency**: Google Drive tests require internet connection
- **Token Costs**: Mode 5/6 tests consume API tokens; use small documents for frequent testing

## License

MIT License - See LICENSE file for details.

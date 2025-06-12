# Multi-Mode Text Enrichment System

## Overview

A sophisticated text enrichment API and web application leveraging the Groq LLM API to provide intelligent, on-demand text generation and enhancement across four specialized modes. Built with FastAPI and modern web technologies, this system offers a flexible, user-friendly interface for various text processing needs.

## Features

### Core Capabilities

- **Four Specialized Enrichment Modes:**
  1. **Context-Aware Completion**: Enhances and continues long-form text while preserving style and context
  2. **Structured Context Enrichment**: Expands content based on topic and context parameters
  3. **Input Refinement**: Polishes and clarifies messy or incomplete text
  4. **Payload Description Agent**: Converts structured JSON data into natural language descriptions

### Technical Features

- **On-Demand Generation**
  - Fresh suggestions generated for each request
  - No persistent storage of suggestions
  - Dynamic response generation

- **Intelligent Processing**
  - Context preservation across generations
  - Adaptive tone and style matching
  - Structured data interpretation

- **Dynamic Parameters**
  - Mode-specific minimum word requirements
  - Configurable output length (words/characters)
  - Adjustable generation parameters per mode

### User Interface

- Modern, responsive web interface
- Real-time validation and feedback
- Adaptive input forms based on mode
- Clear mode descriptions and instructions
- Mobile-friendly design

## Project Structure

```plaintext
Text-Autocompletion-Agent/
├── handlers/
│   └── autocomplete.py         # FastAPI router for enrichment endpoints
├── logic/
│   ├── mode_1.py               # Context-Aware Completion logic
│   ├── mode_2.py               # Structured Context Enrichment logic
│   ├── mode_3.py               # Input Refinement logic
│   └── mode_4.py               # Payload Description Agent logic
├── utils/
│   ├── generator.py            # Groq LLM API integration
│   └── validator.py            # Input validation utilities
├── main.py                     # FastAPI app entry point
├── index.html                  # Frontend web UI
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables (not committed)
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

1. **Environment Variables**
   - `GROQ_API_KEY`: Your Groq API key (required)

2. **Model Parameters** (in `utils/generator.py`)
   - Temperature settings per mode
   - Token limits and generation parameters
   - Model selection options

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

Main endpoint for text enrichment and generation.

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

### `GET /health`

Returns API health status and supported features.

## Enrichment Modes

### 1. Context-Aware Completion (mode_1)

- **Purpose:** Enhance and continue long-form text
- **Input:** text (min 20 words)
- **Use Cases:** Blog posts, articles, narratives
- **Features:** Style matching, context preservation

### 2. Structured Context Enrichment (mode_2)

- **Purpose:** Generate content from topic and context
- **Input:** header (topic) + text (context)
- **Min Words:** 2 combined
- **Use Cases:** Topic expansion, content development

### 3. Input Refinement (mode_3)

- **Purpose:** Clean and polish unclear text
- **Input:** text (no min requirement)
- **Use Cases:** Note refinement, grammar correction
- **Features:** Structure improvement, clarity enhancement

### 4. Payload Description Agent (mode_4)

- **Purpose:** Generate descriptions from JSON data
- **Input:** header (context) + body (JSON)
- **Min Words:** 2 combined
- **Use Cases:** Data summarization, report generation

## Frontend Usage

1. **Mode Selection:**
   - Choose from four specialized modes
   - Read mode descriptions for guidance

2. **Input Forms:**
   - Fill in required fields (varies by mode)
   - Follow minimum word requirements
   - Optional: Set output length limits

3. **Generation:**
   - Click "Generate" for initial suggestion
   - Use "Generate Another" for alternatives
   - "Clear Results" to start fresh

4. **Validation:**
   - Real-time input validation
   - Error messages for invalid input
   - Word count tracking

## Extending the System

### Adding New Modes

1. Create new logic file in `logic/`
2. Add mode to `handlers/autocomplete.py`
3. Update validation in `utils/validator.py`
4. Add UI elements in `index.html`

### Customizing Generation

- Modify model parameters in `utils/generator.py`
- Adjust temperature and top_p per mode
- Configure token limits and constraints

### Adding Validation Rules

- Update `utils/validator.py`
- Add mode-specific requirements
- Implement new validation functions

## License

[Your License Type] - See LICENSE file for details.
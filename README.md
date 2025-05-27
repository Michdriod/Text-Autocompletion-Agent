# Text Autocompletion Service

A powerful text enrichment and completion service built with FastAPI and Groq LLM. This service provides multiple modes of text enhancement, from context-aware completion to structured enrichment and text refinement.

## Features

The service offers three distinct modes of text enrichment:

1. **Context-Aware Completion (Mode 1)**
   - Intelligently continues text based on given context
   - Maintains style, tone, and semantics
   - Generates natural, logical continuations
   - Supports regeneration for alternative completions

2. **Structured Context Enrichment (Mode 2)**
   - Enhances text based on provided header/topic context
   - Maintains topic alignment
   - Enriches content without introducing irrelevant information
   - Supports regeneration for alternative enrichments

3. **Flexible Input Refinement (Mode 3)**
   - Improves and polishes messy or incomplete text
   - Maintains original meaning while enhancing clarity
   - Focuses on grammar, structure, and coherence
   - Ideal for cleaning up rough drafts or notes

## Prerequisites

- Python 3.8+
- Groq API key
- FastAPI
- Uvicorn
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Text-Autocompletion-Service
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your Groq API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

## Usage

1. Start the server:
   ```bash
   python main.py
   ```
   The server will start at `http://localhost:8000`

2. API Endpoints:

   - **Health Check**

     ```http
     GET /health
     ```

   - **Text Enrichment**

     ```http
     POST /autocomplete
     Content-Type: application/json

     {
       "text": "Your input text here...",
       "mode": "mode_1",  // or "mode_2" or "mode_3"
       "header": "Optional header for mode_2",
       "regenerate": false,
       "max_tokens": 50
     }
     ```

   - **Get Suggestions**

     ```http
     GET /suggestions/{mode}?text=your_text&header=optional_header
     ```

   - **Clear Suggestions**

     ```http
     DELETE /suggestions/{mode}?text=your_text&header=optional_header
     ```

## API Parameters

- `text`: Input text to be enriched (minimum 23 words required for modes 1 and 3, minimum 2 words for mode 2)
- `mode`: Enrichment mode ("mode_1", "mode_2", or "mode_3")
- `header`: Required for mode_2, provides topic/context
- `regenerate`: Boolean to generate alternative completions (not supported in mode_3)
- `max_tokens`: Maximum length of generated text (default: 50)

## Project Structure

```
Text-Autocompletion-Service/
├── main.py                 # FastAPI application entry point
├── handlers/
│   └── autocomplete.py     # Request handling and routing
├── logic/
│   ├── mode_1.py          # Context-aware completion logic
│   ├── mode_2.py          # Structured enrichment logic
│   └── mode_3.py          # Text refinement logic
├── utils/
│   ├── generator.py       # Groq LLM API wrapper
│   └── validator.py       # Text validation utilities
├── requirements.txt       # Project dependencies
└── README.md             # This file
```

## Error Handling

The service includes comprehensive error handling for:
- Invalid input validation
- API communication errors
- Mode-specific requirements
- Server errors

## Development

To contribute to the project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Groq LLM](https://groq.com/)
- Uses [Uvicorn](https://www.uvicorn.org/) as the ASGI server
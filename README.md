# Multi-Mode Text Enrichment System

## Overview

This project is an advanced, modular text enrichment API and web application. It leverages the Groq LLM API to provide intelligent, on-demand text generation and enrichment across four distinct operational modes. Each mode is tailored for a specific use case, with robust input validation, dynamic parameter support, and a modern, user-friendly frontend.

---

## Features

- **Four Enrichment Modes:**  
  1. **Context-Aware Completion**: Enhance and continue long-form text.
  2. **Structured Context Enrichment**: Expand on a topic using a header and context.
  3. **Input Refinement**: Clean up and clarify messy or incomplete input.
  4. **Payload Description Agent**: Generate natural language descriptions from structured JSON data and a high-level context header.

- **On-Demand Generation:**  
  Each suggestion is generated fresh from the LLM. No suggestions are stored persistently.

- **Dynamic Parameters:**  
  - Minimum input word count (per mode, can be overridden).
  - Maximum output length (in words or characters).

- **Frontend:**  
  - Modern, responsive UI.
  - Mode selector and adaptive input forms.
  - "Generate Another" for fresh suggestions.
  - "Use This Suggestion" button for user workflow integration.
  - Real-time validation and error feedback.

- **Backend:**  
  - FastAPI-based, modular, and extensible.
  - Strict input validation per mode.
  - Clean separation of logic for each mode.
  - Robust error handling and Groq API integration.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [API Endpoints](#api-endpoints)
- [Enrichment Modes](#enrichment-modes)
- [Frontend Usage](#frontend-usage)
- [Extending the System](#extending-the-system)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Project Structure

```
Text-Autocompletion-Agent/
├── handlers/
│   └── autocomplete.py         # FastAPI router for enrichment endpoints
├── logic/
│   ├── mode_1.py               # Context-Aware Completion logic
│   ├── mode_2.py               # Structured Context Enrichment logic
│   ├── mode_3.py               # Input Refinement logic
│   └── mode_4.py               # Payload Description Agent logic
├── utils/
│   ├── generator.py            # Groq LLM API integration and generation utilities
│   └── validator.py            # Input validation utilities
├── main.py                     # FastAPI app entry point
├── index.html                  # Frontend web UI
├── requirements.txt            # Python dependencies
├── README.md                   # (This file)
└── .env                        # Environment variables (not committed)
```

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Text-Autocompletion-Agent
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your environment variables:**
   - Create a `.env` file in the project root:
     ```
     GROQ_API_KEY=your_groq_api_key_here
     ```

---

## Configuration

- **GROQ_API_KEY**:  
  Required for backend to communicate with the Groq LLM API.  
  Obtain your API key from [Groq](https://groq.com/) and set it in `.env`.

---

## Running the App

1. **Start the backend:**
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

2. **Open the frontend:**
   - Open `index.html` in your browser.
   - Or, serve it with a simple HTTP server:
     ```bash
     python -m http.server
     ```
     Then visit `http://localhost:8000/index.html` (if served from the same directory).

---

## API Endpoints

### `POST /autocomplete`

- **Description:**  
  Main endpoint for text enrichment and generation.

- **Request Body (JSON):**
  - `mode`: `"mode_1"`, `"mode_2"`, `"mode_3"`, or `"mode_4"`
  - `text`: (string, required for modes 1, 2, 3)
  - `header`: (string, required for modes 2, 4)
  - `body`: (object, required for mode 4)
  - `min_input_words`: (int, optional)
  - `max_output_length`: (object, optional, e.g. `{ "type": "words", "value": 50 }`)

- **Response:**
  - `completion`: (string) The generated/enriched text.
  - `mode`: (string) The mode used.

### `GET /health`

- **Description:**  
  Returns API health and supported modes/features.

---

## Enrichment Modes

### 1. Context-Aware Completion (`mode_1`)
- **Purpose:** Enhance and continue long-form user input.
- **Input:** `text` (min 20 words)
- **Output:** Enriched version of the input, preserving context.

### 2. Structured Context Enrichment (`mode_2`)
- **Purpose:** Generate meaningful output from a topic and its context.
- **Input:** `header` (topic), `text` (context). Combined min 2 words.
- **Output:** Text elaborating on the topic using the context.

### 3. Input Refinement (`mode_3`)
- **Purpose:** Clean and refine short, unclear, or messy input.
- **Input:** `text` (no min word requirement)
- **Output:** Clearer, more structured version of the input.

### 4. Payload Description Agent (`mode_4`)
- **Purpose:** Convert structured JSON data into a human-readable description.
- **Input:** `header` (context), `body` (JSON object). Combined min 2 words.
- **Output:** One or more natural language descriptions summarizing the payload.

---

## Frontend Usage

- **Mode Selector:**  
  Choose the enrichment mode at the top of the page.

- **Input Forms:**  
  Fields adapt based on the selected mode (text, header, body).

- **Dynamic Parameters:**  
  Set minimum input words and output length (words/characters).

- **Generate/Regenerate:**  
  - Click "Generate" to get a suggestion.
  - Click "Generate Another" for a fresh suggestion (no suggestions are stored).
  - Click "Use This Suggestion" to select a result for your workflow.

- **Validation:**  
  The UI enforces all input requirements and displays errors if validation fails.

---

## Extending the System

- **Add New Modes:**  
  - Create a new logic file in `logic/`.
  - Add mode handling in `handlers/autocomplete.py` and `utils/validator.py`.
  - Update the frontend to add a new mode button and input fields.

- **Change Model or Parameters:**  
  - Update `utils/generator.py` to adjust model selection or generation parameters.

- **Customize Validation:**  
  - Edit `utils/validator.py` for new rules.

---

## Troubleshooting

- **Backend won't start:**  
  - Check for syntax errors or missing imports.
  - Ensure `.env` exists and `GROQ_API_KEY` is set.

- **Frontend can't connect:**  
  - Make sure backend is running at `http://localhost:8000`.
  - Check browser console and network tab for errors.

- **Groq API errors:**  
  - Ensure your API key is valid and has quota.
  - Check backend logs for error details.

- **Validation errors:**  
  - Ensure you meet the minimum word and required field requirements for each mode.

---

## License

This project is licensed under the MIT License.

---

**For further help, open an issue or contact the maintainer.**
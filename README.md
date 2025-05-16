# Text-Autocompletion-AgentGroq Autocomplete Demo

This is a simple text autocompletion system that uses Groq's LLM API with the mixtral-8x7b-32768 model.
Setup Instructions
Backend Setup

Install Python dependencies:
bashpip install fastapi uvicorn httpx python-dotenv

Create a .env file in the project root with your Groq API key:
GROQ_API_KEY=your_groq_api_key_here

Start the FastAPI server:
bashuvicorn main:app --reload


Frontend Setup

Simply open index.html in your browser or serve it using a simple HTTP server:
bashpython -m http.server 8080

Access the application at http://localhost:8080

How It Works

User types in the text field
After a 300ms debounce delay, the text is sent to the backend API
The backend calls Groq's API to generate text completion
The suggested completion is displayed in real-time beneath the input
Only the autocompleted portion is highlighted for clarity

File Structure

main.py - FastAPI backend server
index.html - Frontend HTML and JavaScript
.env - Environment variables (not committed to git)






# Text Autocompletion Agent

A real-time text autocompletion system that enriches text as you write, providing relevant suggestions and content enhancements.

## Features

- **Real-time suggestions**: Get text completions as you type
- **Two completion modes**:
  - **Simple mode**: Straightforward text completions that follow your writing style
  - **Enriched mode**: Enhanced completions with more context, details, and descriptions
- **Customizable token length**: Control how long suggestions can be
- **Easy acceptance**: Press Tab or click a button to accept suggestions

## Setup

### Prerequisites

- Python 3.8+
- A Groq API key (sign up at [groq.com](https://console.groq.com/))

### Installation

1. Clone this repository
2. Install dependencies:
```
pip install fastapi uvicorn httpx python-dotenv
```

3. Create a `.env` file in the project root with your Groq API key:
```
GROQ_API_KEY=your_groq_api_key_here
```

### Running the Application

1. Start the backend server:
```
python main.py
```

2. Open `index.html` in your web browser
   - You can use any simple HTTP server to serve this file, such as:
   ```
   python -m http.server
   ```
   - Then navigate to http://localhost:8000 in your browser

## How It Works

The application consists of:

1. **Frontend**: A simple HTML/CSS/JavaScript interface that captures user input and displays suggestions
2. **Backend**: A FastAPI server that processes text and communicates with the Groq API
3. **LLM**: Groq's Mixtral-8x7b-32768 model which generates the text completions

The system waits for you to pause typing, then sends your current text to the backend. The backend formats a prompt for the LLM and returns the generated continuation, which appears as a suggestion in the editor.

## Customization

You can modify the backend's `main.py` file to:
- Adjust temperature and other LLM parameters
- Change prompt engineering for different completion styles
- Add more modes beyond simple and enriched
- Integrate with different LLM providers

## License

MIT
# ✈️ ChangiChirp: Your AI Airport Assistant

Welcome to **ChangiChirp** – Your intelligent travel companion for Changi Airport and Jewel Changi! This chatbot leverages the power of Google's Gemini AI and Retrieval-Augmented Generation (RAG) to provide accurate, up-to-date information about your favorite travel hub.

![ChangiChirp UI](https://img.icons8.com/color/96/000000/airport.png)

---

## 🚀 Features
- **Smart Q&A** - Get instant answers about Changi Airport and Jewel Changi
- **Accurate Information** - Powered by Google's Gemini AI with RAG for factual responses
- **Modern UI** - Sleek, responsive interface with airport-themed design
- **Easy to Deploy** - Simple setup with clear documentation
- **Knowledge Base** - Web scraping pipeline to keep information current

---

## 🧠 How It Works
1. **Ask a Question** (e.g., "Where can I find the butterfly garden?")
2. **Retrieval** - The system finds relevant information from the FAISS vector database
3. **Generation** - Google's Gemini AI crafts a natural, helpful response
4. **Verification** - The response is checked for quality and relevance
5. **Delivery** - You receive a clear, accurate answer with source references

---

## 🏗️ Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript
- **AI/ML**: 
  - Google Gemini API for natural language understanding
  - FAISS for efficient vector similarity search
  - LangChain for RAG pipeline
- **Data Processing**: BeautifulSoup4, lxml for web scraping
- **Deployment**: Gunicorn, Uvicorn (ASGI server)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Gemini API key

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ChangiChirp.git
   cd ChangiChirp
   ```

2. **Set up a virtual environment** (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key
   ```

5. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

6. **Open in your browser**:
   ```
   http://localhost:8000
   ```

## 🔄 Updating the Knowledge Base

To update the information the chatbot knows:

```bash
# Run the web scraper
python webscrape.py

# Process the data and update the FAISS index
python ingest.py --data scraped_data.jsonl --out faiss_index
```

## 🧩 Project Structure

```
ChangiChirp/
├── static/               # Frontend static files
│   └── index.html        # Main frontend interface
├── faiss_index/          # Vector store (generated, not in version control)
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
├── ingest.py             # Data ingestion and processing
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
├── webscrape.py          # Web scraper for updating knowledge
└── README.md             # This file
```

## 🤖 Example Questions
- "What are the best food options in Jewel?"
- "Where can I find the butterfly garden?"
- "How do I get from Terminal 1 to Jewel?"
- "What are the operating hours of the rooftop pool?"

---

## 🐞 Troubleshooting

- **API Key Issues**: Ensure your `GEMINI_API_KEY` is set in the `.env` file
- **Missing Dependencies**: Run `pip install -r requirements.txt` if you encounter any import errors
- **Web Scraping**: Some websites may block scrapers - check the `webscrape.py` logs for issues
- **FAISS Index**: If the index is missing or corrupted, re-run `python ingest.py`
- **Port Conflicts**: If port 8000 is in use, specify a different port: `uvicorn main:app --port 8001`

## 🌟 Features in Development
- [ ] Multi-language support
- [ ] Voice interaction
- [ ] Offline mode with local model fallback
- [ ] User authentication and saved preferences
- [ ] Mobile app version

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Bugs**: Open an issue with detailed steps to reproduce
2. **Suggest Features**: Share your ideas for new features
3. **Code Contributions**: Submit pull requests for bug fixes or new features
4. **Improve Documentation**: Help make our docs clearer and more comprehensive

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev/) for the powerful AI capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [FAISS](https://github.com/facebookresearch/faiss) for efficient similarity search
- [Changi Airport](https://www.changiairport.com/) for being an amazing travel hub
- All contributors who help improve this project

## 📬 Contact

Have questions or suggestions? Open an issue or reach out to the maintainers.

---

## ✨ Happy Travels with ChangiChirp! ✈️

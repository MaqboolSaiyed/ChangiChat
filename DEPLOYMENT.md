# ChangiChirp Deployment Guide

## 🚀 Deploy to Render (Free Tier)

### Prerequisites
1. GitHub account
2. Render account (free tier available)
3. Google Gemini API key

### Step 1: Prepare Your Repository
1. Push your code to GitHub
2. Make sure all files are committed
3. Ensure `.env` file is NOT in the repository (use Render's environment variables instead)

### Step 2: Deploy on Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `changi-chirp` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

### Step 3: Environment Variables
Add these environment variables in Render dashboard:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `PORT`: `10000` (Render will set this automatically)

### Step 4: Deploy
1. Click "Create Web Service"
2. Wait for deployment to complete (5-10 minutes)
3. Your app will be available at the provided URL

## 🔧 Local Development

### Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd ChangiChirp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-api-key-here"  # On Windows: set GEMINI_API_KEY=your-api-key-here

# Run the application
python main.py
```

### Access the Application
- Local: `http://127.0.0.1:8000`
- Production: Your Render URL

## 📁 Project Structure
```
ChangiChirp/
├── main.py              # FastAPI application
├── webscrape.py         # Web scraping script
├── ingest.py           # Data ingestion script
├── requirements.txt    # Python dependencies
├── Procfile           # Process configuration
├── render.yaml        # Render configuration
├── gunicorn_config.py # Gunicorn settings
├── .gitignore         # Git ignore rules
├── README.md          # Project documentation
└── DEPLOYMENT.md      # This file
```

## 🛠️ Features
- **Modern UI**: Beautiful dark theme with golden accents
- **AI-Powered**: Uses Google Gemini 2.0 Flash
- **Responsive**: Works on desktop and mobile
- **Fast**: Optimized for performance
- **Free Hosting**: Runs on Render's free tier

## 🔑 API Endpoints
- `GET /`: Redirects to chat interface
- `GET /chat-ui`: Main chat interface
- `POST /chat`: Chat API endpoint

## 📝 Notes
- The application uses direct Gemini API calls (no vector database for simplicity)
- All UI is inline HTML/CSS/JS for easy deployment
- Optimized for Render's free tier limitations
- No database required - stateless application

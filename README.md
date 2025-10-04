# Instagram Scraper App

Modern Instagram scraping application with React frontend and FastAPI backend.

## 🚀 Features

- **Instagram Profile Scraping**: Extract user profiles, posts, and engagement data
- **Message Sending**: Send direct messages to Instagram users
- **Analytics Dashboard**: Visualize user engagement and performance metrics
- **User Management**: Manage scraped user data
- **Modern UI**: Beautiful React interface with Ant Design components

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Ant Design
- **Backend**: FastAPI + Python
- **Database**: Supabase (PostgreSQL)
- **Scraping**: Selenium + Apify
- **Deployment**: Vercel

## 📦 Installation

### Prerequisites
- Node.js 16+
- Python 3.9+
- npm or yarn

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the API server
python api.py
# or
uvicorn api:app --reload
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 🔧 Environment Variables

Create a `.env` file in the root directory:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
APIFY_API_TOKEN=your_apify_token
UNIPILE_API_KEY=your_unipile_key
UNIPILE_BASE_URL=your_unipile_base_url
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
```

## 🚀 Deployment

### Vercel Deployment
1. Push your code to GitHub
2. Connect your repository to Vercel
3. Set environment variables in Vercel dashboard
4. Deploy!

### Manual Deployment
```bash
# Build frontend
cd frontend && npm run build

# Deploy backend
# Your preferred hosting service (Heroku, Railway, etc.)
```

## 📱 Usage

1. **Dashboard**: View overall statistics and activity
2. **Scraper**: Enter Instagram username to scrape profile data
3. **Messages**: Send direct messages to Instagram users
4. **Analytics**: Analyze user engagement and performance
5. **Users**: Manage scraped user data

## 🛠️ API Endpoints

- `GET /` - Health check
- `POST /scrape/profile` - Scrape Instagram profile
- `POST /scrape/posts` - Scrape Instagram posts
- `POST /send/message` - Send Instagram message
- `GET /users` - Get all users
- `GET /users/{username}` - Get specific user
- `GET /analytics/{username}` - Get user analytics
- `GET /dashboard/stats` - Get dashboard statistics

## 🔒 Security

- Environment variables for sensitive data
- CORS configuration for frontend-backend communication
- Input validation with Pydantic models
- Error handling and logging

## 📄 License

This project is for educational purposes only. Please respect Instagram's Terms of Service and use responsibly.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## ⚠️ Disclaimer

This tool is for educational purposes only. Users are responsible for complying with Instagram's Terms of Service and applicable laws. The developers are not responsible for any misuse of this application.
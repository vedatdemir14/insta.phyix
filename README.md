# PhyixInsta - Instagram Scraper & Nationality Classification

A comprehensive web application for Instagram profile scraping, nationality classification, and automated messaging campaigns.

## 🚀 Features

### Core Functionality
- **Instagram Profile Scraping**: Automated extraction of profile data using Selenium and Apify API
- **AI-Powered Nationality Classification**: Machine learning-based nationality detection (TÜRK/YABANCI)
- **Multi-language Message Campaigns**: DeepL integration for automatic message translation
- **Session Management**: Organized data storage with session-based categorization
- **Real-time Analytics**: Dashboard with comprehensive statistics

### Technical Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React 18 + TypeScript
- **Database**: Supabase (PostgreSQL)
- **AI/ML**: OpenRouter API for nationality classification
- **Translation**: DeepL API for multi-language support
- **Scraping**: Selenium WebDriver + Apify API

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- Chrome/Chromium browser
- Git

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/vedatdemir14/phyixinsta.git
cd phyixinsta

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="your_supabase_url"
export SUPABASE_API_KEY="your_supabase_key"
export APIFY_API_TOKEN="your_apify_token"
export OPENROUTER_API_KEY="your_openrouter_key"
export DEEPL_API_KEY="your_deepl_key"

# Run the backend
python api.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 📊 Database Schema

### Leads Table
```sql
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    posts_count INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    profile_pic_url TEXT,
    nationality VARCHAR(255),
    session_name VARCHAR(255),
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    session_name VARCHAR(255) NOT NULL,
    lead_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);
```

### Instagram Accounts Table
```sql
CREATE TABLE instagram_accounts (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);
```

## 🔧 API Endpoints

### Profile Scraping
- `POST /campaigns/profile-scraping` - Scrape Instagram profiles
- `POST /campaigns/location-scraping` - Location-based scraping

### Nationality Classification
- `POST /campaigns/nationality-classification` - Classify user nationalities
- `POST /leads/update-nationality` - Update nationality data

### Message Campaigns
- `POST /campaigns/message-campaign` - Send message campaigns
- `GET /message-templates` - Get message templates
- `POST /message-templates` - Create new templates

### Data Management
- `GET /leads` - Get all leads
- `GET /leads/sessions` - Get all sessions
- `GET /instagram-accounts` - Get Instagram accounts

## 🎯 Usage

### 1. Profile Scraping
1. Navigate to **Campaigns** → **Profile Scraping**
2. Enter target usernames or use location scraping
3. Configure scraping parameters
4. Start the scraping process

### 2. Nationality Classification
1. Go to **Campaigns** → **Nationality Classification**
2. Select scraped profiles
3. Run AI-powered nationality analysis
4. Review and edit results if needed

### 3. Message Campaigns
1. Access **Campaigns** → **Message Campaign**
2. Create or select message templates
3. Filter leads by nationality (Turkish/Foreign)
4. Configure campaign settings
5. Launch automated messaging

## 🔒 Security Features

- **Row Level Security (RLS)**: Supabase-based access control
- **JWT Authentication**: Secure session management
- **API Key Management**: Encrypted credential storage
- **Input Validation**: Comprehensive data validation
- **Rate Limiting**: Protection against API abuse

## 📈 Performance Optimizations

- **Async/Await**: Non-blocking operations
- **Connection Pooling**: Efficient database connections
- **Caching**: Redis-based caching system
- **Batch Processing**: Bulk data operations
- **Code Splitting**: Optimized frontend loading

## 🧪 Testing

### Backend Testing
```bash
# Run API tests
pytest tests/

# Run specific test modules
pytest tests/test_api.py
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 🚀 Deployment

### VPS Deployment
1. **Server Requirements**: Ubuntu 20.04+, 2GB RAM, 30GB SSD
2. **Install Dependencies**: Python 3.9+, Node.js 18+, Chrome
3. **Database Setup**: Configure Supabase connection
4. **Nginx Configuration**: Reverse proxy setup
5. **SSL Certificate**: Let's Encrypt integration

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Vedat Demir** - *Initial work* - [vedatdemir14](https://github.com/vedatdemir14)

## 🙏 Acknowledgments

- Supabase for database services
- DeepL for translation services
- Apify for Instagram scraping
- OpenRouter for AI classification
- React and FastAPI communities

## 📞 Support

For support and questions:
- Email: [your-email@domain.com]
- GitHub Issues: [Create an issue](https://github.com/vedatdemir14/phyixinsta/issues)

---

**PhyixInsta** - Advanced Instagram Analytics & Automation Platform
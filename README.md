
# 🚀 Advanced Email Campaign System

A powerful email marketing automation system with AI-powered personalization, campaign analytics, A/B testing, and performance tracking. Built using Python, Streamlit, and integrations with external services like SerpAPI, GROQ, Mailjet, and Google Sheets.

---

## 📌 Features

- ✅ **AI-Powered Personalized Email Generation**
- 📨 **Bulk Email Sending with Deliverability Checks**
- 🔍 **Email Finder Tool Using Web Search & AI Extraction**
- 🧪 **A/B Testing for Email Campaigns**
- 📊 **Comprehensive Dashboard & Analytics**
- ⏱️ **Campaign Scheduling**
- 📝 **Template Builder with Spam Score Checker**
- 📈 **Performance Tracking (Best Times, Deliverability)**
- 📁 **Excel/CSV & Google Sheets Integration**

---

## 🛠 Requirements

Make sure you have the following installed:

- 🐍 **Python 3.9+**
- 📦 **pip** or **poetry** for dependency management
- 🗃️ **SQLite** (for local tracking logs)
- 📎 Required Libraries:
  - `streamlit`
  - `pandas`
  - `requests`
  - `gspread`, `gspread-dataframe`
  - `serpapi`
  - `python-dotenv`
  - `smtplib`, `email`
  - `schedule`
  - `plotly`
  - `sqlite3`
  - `pathlib`

Install dependencies via:

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in your root directory with the following keys:

```env
SERP_API_KEY=your_serpapi_key_here
GROQ_API_KEY=your_groq_api_key_here
MAILJET_API_KEY=your_mailjet_api_key
MAILJET_SECRET_KEY=your_mailjet_secret_key
EMAIL=your_sender_email@example.com
SERVICE_ACCOUNT_FILE=path/to/Credentials.json
```

---

## 🧩 Project Structure

```
.
├── app.py                  # Main application script
├── Credentials.json        # Google Sheets API key
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🧪 How to Run

1. Start the Streamlit app:

```bash
streamlit run app.py
```

2. Open the browser window that opens automatically.

3. Use the sidebar to navigate between different modules:
   - Dashboard
   - Send Emails
   - Email Finder
   - Template Builder
   - A/B Testing
   - Schedule Campaigns
   - Performance Tracking

---

## 📤 Sending Emails

### Prerequisites
- ✅ Valid Mailjet credentials
- ✅ Proper email templates
- ✅ Recipient data in Excel/CSV or Google Sheets

### Steps
1. Upload your Excel/CSV file or connect a Google Sheet.
2. Select or build your email template.
3. Choose whether to use AI-powered personalization.
4. Click "Send Campaign" and monitor progress.

---

## 🔍 Email Finder

Use this tool to find missing email addresses by searching company information online and extracting contact details with AI.

### Bulk Mode
- Upload a list of companies.
- Set search type (e.g., sales@, support@).
- Configure rate limits to avoid hitting API caps.

---

## 🧠 AI-Powered Templates

The system uses GROQ’s LLM API to generate highly personalized emails based on company data. You can also create custom templates manually.

---

## 📊 Campaign Analytics

View real-time statistics including:
- Total emails sent
- Success/failure rates
- Primary inbox vs spam delivery
- Daily sending trends
- Best times to send emails

---

## 🧪 A/B Testing

Compare two versions of your email content to see which performs better. The system tracks open/click rates and engagement metrics.

---

## ⏱️ Scheduled Campaigns

Schedule campaigns to send at a future date/time. Ideal for timed promotions or international time zone considerations.

---

## 📁 Data Sources

- **Excel/CSV Files**: For uploading lists of recipients.
- **Google Sheets**: Real-time sync and updates.
- **Local SQLite DB**: Tracks sent emails, statuses, and deliverability.

---

## 📈 Deliverability Optimization

- 🧼 **Spam Score Checker** for subject/body
- 📬 **Email Validation** before sending
- 📞 **Domain Type Detection** (personal vs business)
- 🚫 **Disposable Email Filtering**

---

## 📦 Deployment

For production deployment:

- Use **Streamlit Community Cloud**, **Heroku**, or **Docker**
- Ensure environment variables are set securely
- Set up persistent storage for SQLite database if needed
- Consider using cloud-hosted databases for scalability

---

## 📄 License

MIT License – see [LICENSE](LICENSE)

---

## 💬 Questions?

If you have any questions or need help setting up the system, feel free to reach out or submit an issue.

---

## ✅ Acknowledgments

This system integrates multiple APIs and tools:
- SerpAPI: Web search for email discovery
- GROQ: AI content generation
- Mailjet: Email delivery
- Google Sheets API: Data integration
- Streamlit: UI framework

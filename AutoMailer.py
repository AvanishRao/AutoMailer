import pandas as pd

import requests

import streamlit as st

from serpapi import GoogleSearch

import gspread

from gspread_dataframe import set_with_dataframe

from dotenv import load_dotenv

import os

import time

import smtplib

from email.mime.multipart import MIMEMultipart

from email.mime.text import MIMEText

from email.mime.base import MIMEBase

from email import encoders

import schedule

import threading

import re

import plotly.express as px

import plotly.graph_objects as go

from datetime import datetime, timedelta

import uuid

import sqlite3

from pathlib import Path

import base64

from urllib.parse import quote



# Load environment variables

load_dotenv()



# API Keys

SERP_API_KEY = os.getenv("SERP_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SERVICE_ACCOUNT_FILE = "C:\\Users\\acer\\AutoMail\\Credentials.json"

EMAIL = os.getenv("EMAIL")

MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")

MAILJET_SECRET_KEY = os.getenv("MAILJET_SECRET_KEY")



# Database setup for email tracking

def init_database():

    """Initialize SQLite database for email tracking"""

    db_path = Path("email_tracking.db")

    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    

    cursor.execute('''

        CREATE TABLE IF NOT EXISTS email_logs (

            id TEXT PRIMARY KEY,

            recipient_email TEXT,

            company_name TEXT,

            subject TEXT,

            sent_time TIMESTAMP,

            status TEXT,

            delivery_status TEXT,

            opened BOOLEAN DEFAULT FALSE,

            clicked BOOLEAN DEFAULT FALSE,

            bounced BOOLEAN DEFAULT FALSE,

            spam_score REAL,

            error_message TEXT

        )

    ''')

    

    conn.commit()

    conn.close()



def log_email_status(email_id, recipient_email, company_name, subject, status, delivery_status="pending", error_message=None):

    """Log email status to database"""

    conn = sqlite3.connect("email_tracking.db")

    cursor = conn.cursor()

    

    cursor.execute('''

        INSERT OR REPLACE INTO email_logs 

        (id, recipient_email, company_name, subject, sent_time, status, delivery_status, error_message)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    ''', (email_id, recipient_email, company_name, subject, datetime.now(), status, delivery_status, error_message))

    

    conn.commit()

    conn.close()



def get_email_stats():

    """Get email statistics from database"""

    conn = sqlite3.connect("email_tracking.db")

    df = pd.read_sql_query("SELECT * FROM email_logs ORDER BY sent_time DESC", conn)

    conn.close()

    return df



# Email validation function (enhanced)

def is_valid_email(email):

    """Enhanced email validation"""

    if not email or pd.isna(email):

        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    return re.match(pattern, str(email)) is not None



def validate_email_deliverability(email):

    """Check email deliverability factors"""

    score = 100

    warnings = []

    

    # Check for disposable email domains

    disposable_domains = ['temp-mail.org', '10minutemail.com', 'guerrillamail.com', 'mailinator.com']

    if any(domain in email.lower() for domain in disposable_domains):

        score -= 30

        warnings.append("Disposable email domain")

    

    # Check for common personal domains vs business domains

    personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']

    if any(domain in email.lower() for domain in personal_domains):

        score -= 10

        warnings.append("Personal email domain - may have stricter spam filters")

    

    return score, warnings



# Enhanced data processing functions

def find_email_column(df):

    """Automatically detect email column in the dataframe"""

    possible_email_columns = ['email', 'gmail', 'mail', 'e-mail', 'email_address', 'contact_email', 'business_email']

    

    # Check for exact matches first

    for col in df.columns:

        if col.lower() in possible_email_columns:

            return col

    

    # Check for partial matches

    for col in df.columns:

        if any(email_term in col.lower() for email_term in ['email', 'mail', 'gmail']):

            return col

    

    # Check column content for email patterns

    for col in df.columns:

        if df[col].dtype == 'object':

            sample_values = df[col].dropna().head(10)

            email_count = sum(1 for val in sample_values if is_valid_email(str(val)))

            if email_count > len(sample_values) * 0.5:  # If more than 50% look like emails

                return col

    

    return None



def find_company_name_column(df):

    """Automatically detect company name column in the dataframe"""

    possible_company_columns = ['company', 'company_name', 'business', 'organization', 'org', 'firm', 'business_name', 'name']

    

    # Check for exact matches first

    for col in df.columns:

        if col.lower() in possible_company_columns:

            return col

    

    # Check for partial matches

    for col in df.columns:

        if any(company_term in col.lower() for company_term in ['company', 'business', 'organization', 'name']):

            return col

    

    # Return first column if no obvious match

    return df.columns[0] if len(df.columns) > 0 else None



def process_excel_data(df):

    """Process Excel data to ensure email column exists and extract company information"""

    processed_df = df.copy()

    

    # Find existing email column

    email_col = find_email_column(processed_df)

    company_col = find_company_name_column(processed_df)

    

    # If no email column found, create one

    if email_col is None:

        processed_df['Gmail'] = ''

        email_col = 'Gmail'

        st.warning("No email column found. Created 'Gmail' column. You may need to fill it manually or use search functionality.")

    else:

        # Rename to standardize

        if email_col != 'Gmail':

            processed_df['Gmail'] = processed_df[email_col]

    

    # Ensure company name column exists

    if company_col is None:

        company_col = processed_df.columns[0]

        st.info(f"Using '{company_col}' as company name column.")

    

    return processed_df, email_col, company_col



def create_comprehensive_company_info(row, company_col):

    """Create comprehensive company information string from all available data"""

    company_name = str(row.get(company_col, 'Unknown Company'))

    

    # Exclude email and company name columns from additional info

    excluded_cols = ['Gmail', 'gmail', 'email', 'Email', company_col]

    

    info_parts = [f"Company Name: {company_name}"]

    

    for col, value in row.items():

        if col not in excluded_cols and pd.notna(value) and str(value).strip():

            clean_value = str(value).strip()

            if clean_value and clean_value.lower() not in ['nan', 'none', 'null', '']:

                info_parts.append(f"{col}: {clean_value}")

    

    return "\n".join(info_parts)



# Enhanced Google Sheets functions

def authenticate_google_sheets():

    try:

        client = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)

        return client

    except Exception as e:

        st.error(f"Authentication Error: {str(e)}")

        return None



def load_google_sheet(sheet_url):

    try:

        gc = authenticate_google_sheets()

        if gc is None:

            return None, None, None

        sheet_key = sheet_url.split('/d/')[1].split('/')[0]

        sheet = gc.open_by_key(sheet_key)

        worksheet = sheet.get_worksheet(0)

        data = worksheet.get_all_records()

        return pd.DataFrame(data), gc, worksheet

    except Exception as e:

        st.error(f"Error loading sheet: {str(e)}")

        return None, None, None



def update_google_sheet(worksheet, results_df):

    try:

        data = [results_df.columns.values.tolist()]

        data.extend(results_df.values.tolist())

        worksheet.clear()

        worksheet.update('A1', data)

        return True, "Google Sheet updated successfully!"

    except Exception as e:

        detailed_error = f"Error updating sheet: {str(e)}"

        st.error(detailed_error)

        return False, detailed_error



# Enhanced search functions for missing emails

def get_search_results(query, prompt, api_key, column_name):

    try:

        search_query = prompt.format(column_name=query)

    except KeyError:

        search_query = prompt.replace("{col_name}", query).replace("{column_name}", query)



    params = {

        "engine": "google",

        "q": search_query,

        "num": 100,

        "api_key": api_key

    }



    search = GoogleSearch(params)

    results = search.get_dict()



    text_content = ""

    if "knowledge_graph" in results:

        knowledge = results["knowledge_graph"]

        for key in ["title", "type", "website", "founded", "headquarters", "revenue",

                    "social", "mobile", "phone", "ceo", "email", "contact email",

                    "address", "contact", "call", "chat", "connect", "write",

                    "twitter", "instagram", "facebook"]:

            text_content += f"{knowledge.get(key, '')}\n"



    for result in results.get("organic_results", []):

        text_content += f"{result.get('title', 'N/A')} - {result.get('snippet', 'N/A')}\n"



    return text_content



def ask_groq_api(question, company, context, api_key):

    headers = {

        "Authorization": f"Bearer {api_key}",

        "Content-Type": "application/json"

    }

    prompt = f"""

    You are an AI assistant specialized in extracting specific information from any data.

    From the context and question provided, extract only the feature which is asked in the question.

    Respond only with the asked feature, without any verbosity. Clean and exact answers only.



    Question: {question}

    Company: {company}

    Context: {context}

    """

    payload = {

        "model": "llama3-8b-8192",

        "messages": [

            {"role": "system", "content": "You are an assistant that extracts specific information from context."},

            {"role": "user", "content": prompt}

        ]

    }

    wait_time = 30

    max_retries = 5



    for attempt in range(max_retries):

        try:

            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)

            if response.status_code == 200:

                response_json = response.json()

                return response_json['choices'][0]['message']['content'].strip()

            elif response.status_code == 429:

                print(f"Rate limit reached. Waiting for {wait_time} seconds before retrying...")

                time.sleep(wait_time)

                wait_time *= 2

            else:

                return f"Error: {response.status_code}, {response.text}"

        except Exception as e:

            return f"Error: {str(e)}"

    return "Error: Max retries exceeded. Please try again later."



def generate_email_content(template, company_name, company_info, api_key):

    """Generate personalized email content using comprehensive company data"""

    headers = {

        "Authorization": f"Bearer {api_key}",

        "Content-Type": "application/json"

    }

    

    prompt = f"""

    You are an expert email writer specializing in business communications that avoid spam filters.

    Generate a professional, personalized email that follows these deliverability best practices:



    Template/Instructions: {template}

    

    Company Information (use this to personalize the email):

    {company_info}

    

    IMPORTANT DELIVERABILITY RULES:

    1. Use professional, conversational tone (not overly salesy)

    2. Avoid spam trigger words like "FREE", "URGENT", "GUARANTEED", excessive exclamation marks

    3. Include specific, relevant details about the company from the provided information

    4. Make it sound like genuine business correspondence

    5. Keep subject line under 50 characters

    6. Use proper sentence structure and grammar

    7. Include a clear but subtle call-to-action

    8. Personalize with specific company details from the provided information

    9. Reference specific company attributes like industry, location, size, etc. when available

    

    Generate only the email content without any additional text or explanations.

    Make sure to use the company information provided to create a highly personalized message.

    """

    

    payload = {

        "model": "llama3-8b-8192",

        "messages": [

            {"role": "system", "content": "You are a professional email writer who creates highly personalized, spam-filter-friendly business emails using comprehensive company data."},

            {"role": "user", "content": prompt}

        ],

        "temperature": 0.7,

        "max_tokens": 1000

    }

    

    wait_time = 30

    max_retries = 3

    

    for attempt in range(max_retries):

        try:

            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)

            if response.status_code == 200:

                response_json = response.json()

                generated_content = response_json['choices'][0]['message']['content'].strip()

                return generated_content

            elif response.status_code == 429:

                print(f"Rate limit reached. Waiting for {wait_time} seconds before retrying...")

                time.sleep(wait_time)

                wait_time *= 2

            else:

                return f"Error generating content: {response.status_code}, {response.text}"

        except Exception as e:

            return f"Error generating content: {str(e)}"

    

    return "Error: Could not generate email content. Please try again later."



def generate_email_subject(template, company_name, company_info, api_key):

    """Generate personalized email subject using comprehensive company data"""

    headers = {

        "Authorization": f"Bearer {api_key}",

        "Content-Type": "application/json"

    }



    prompt = f"""

    Generate a professional email subject line that will pass spam filters.



    Template/Instructions: {template}

    

    Company Information (use this to personalize):

    {company_info}



    DELIVERABILITY RULES:

    1. Keep under 50 characters

    2. Avoid ALL CAPS, excessive punctuation (!!!), and spam words

    3. Make it specific and personalized using the company information

    4. Sound like genuine business correspondence

    5. Include company name or specific detail naturally

    6. Avoid words like: FREE, URGENT, GUARANTEED, AMAZING, INCREDIBLE

    7. Use title case or sentence case

    8. Do not include any newline characters



    Generate only the subject line without any additional text.

    """



    payload = {

        "model": "llama3-8b-8192",

        "messages": [

            {"role": "system", "content": "You are an expert at creating professional, spam-filter-friendly email subject lines using company data."},

            {"role": "user", "content": prompt}

        ],

        "temperature": 0.7,

        "max_tokens": 100

    }



    try:

        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)

        if response.status_code == 200:

            response_json = response.json()

            return response_json['choices'][0]['message']['content'].strip().replace('\n', '')

        else:

            return template.replace("{company_name}", company_name)

    except Exception as e:

        return template.replace("{company_name}", company_name)



def create_html_email_body(plain_text, company_name, tracking_id=None):

    """Create HTML email body with better formatting and optional tracking"""

    

    tracking_pixel = f'<img src="https://your-tracking-domain.com/pixel/{tracking_id}" width="1" height="1" style="display:none;">' if tracking_id else ""

    

    html_body = f"""

    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>Email from AutoMail</title>

    </head>

    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">

            <div style="background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">

                <div style="white-space: pre-line; margin-bottom: 20px;">

                    {plain_text}

                </div>

                

                <hr style="border: none; height: 1px; background-color: #e9ecef; margin: 20px 0;">

                

                <div style="font-size: 12px; color: #6c757d; text-align: center;">

                    <p>This email was sent by AutoMail Email System</p>

                    <p>If you'd like to unsubscribe, please reply with "UNSUBSCRIBE" in the subject line.</p>

                </div>

            </div>

        </div>

        {tracking_pixel}

    </body>

    </html>

    """

    return html_body



def send_email_enhanced(receiver_email, subject, body, company_name="Unknown Company"):

    """Enhanced email sending with better deliverability practices"""



    email_id = str(uuid.uuid4())



    # Validate email

    if not is_valid_email(receiver_email):

        log_email_status(email_id, receiver_email, company_name, subject, "failed", "invalid_email", "Invalid email address")

        return False, f"Invalid email address: {receiver_email}", email_id



    # Check deliverability score

    deliverability_score, warnings = validate_email_deliverability(receiver_email)



    # Check if required environment variables are set

    if not EMAIL or not MAILJET_API_KEY or not MAILJET_SECRET_KEY:

        error_msg = "Missing email configuration. Check environment variables."

        log_email_status(email_id, receiver_email, company_name, subject, "failed", "config_error", error_msg)

        return False, error_msg, email_id



    sender_email = EMAIL

    sender_name = "BreakoutAI Team"



    # Create multipart message with both plain text and HTML

    msg = MIMEMultipart('alternative')

    msg['From'] = f"{sender_name} <{sender_email}>"

    msg['To'] = receiver_email



    # Ensure subject line doesn't contain newlines

    clean_subject = subject.replace('\n', '') if subject else f"Partnership Opportunity for {company_name}"

    msg['Subject'] = clean_subject



    # Add custom headers to improve deliverability

    msg['Reply-To'] = sender_email

    msg['Return-Path'] = sender_email

    msg['X-Mailer'] = 'BreakoutAI Email System v2.0'

    msg['X-Priority'] = '3'

    msg['Message-ID'] = f"<{email_id}@breakoutai.com>"



    # Ensure body is not None

    email_body = body if body else "Thank you for your time."



    # Create plain text and HTML versions

    text_part = MIMEText(email_body, 'plain', 'utf-8')

    html_part = MIMEText(create_html_email_body(email_body, company_name, email_id), 'html', 'utf-8')



    # Attach parts

    msg.attach(text_part)

    msg.attach(html_part)



    try:

        # Create SMTP connection with enhanced settings

        server = smtplib.SMTP('in-v3.mailjet.com', 587)

        server.starttls()

        

        # Login with Mailjet credentials

        server.login(MAILJET_API_KEY, MAILJET_SECRET_KEY)

        

        # Send email

        text = msg.as_string()

        server.sendmail(sender_email, receiver_email, text)

        server.quit()

        

        # Log successful send

        delive

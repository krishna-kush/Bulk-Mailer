# 📧 **Professional Email Campaign Manager**

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![SMTP](https://img.shields.io/badge/SMTP-Multi%20Provider-green.svg)
![Threading](https://img.shields.io/badge/Threading-Concurrent-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**🚀 Enterprise-grade email campaign management system**

*Professional bulk email sending with advanced queue management, rate limiting, and intelligent retry mechanisms*

</div>

---

## 📋 **Table of Contents**

- [🎯 What is Email Campaign Manager?](#-what-is-email-campaign-manager)
- [✨ Key Features](#-key-features)
- [🏗️ System Architecture](#️-system-architecture)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Configuration Guide](#️-configuration-guide)
- [📊 Usage Examples](#-usage-examples)
- [🔧 Advanced Features](#-advanced-features)
- [📁 Project Structure](#-project-structure)
- [🛠️ Troubleshooting](#️-troubleshooting)

---

## 🎯 **What is Email Campaign Manager?**

**Email Campaign Manager** is a sophisticated, enterprise-grade email automation platform designed for professional bulk email campaigns. Built with Python, it provides advanced queue management, intelligent rate limiting, and robust error handling for reliable email delivery at scale.

### 🔍 **Core Capabilities:**

1. **📧 Multi-Provider SMTP** - Support for Gmail, Outlook, Yahoo, and custom SMTP servers
2. **⚡ Intelligent Queue Management** - Smart load balancing across multiple senders
3. **🛡️ Advanced Rate Limiting** - Prevent provider blocking with intelligent throttling
4. **🔄 Retry Mechanisms** - Automatic retry with exponential backoff
5. **📊 Real-time Monitoring** - Comprehensive logging and progress tracking
6. **🎨 Template System** - Professional HTML email templates with personalization

### 🎯 **Perfect For:**
- 📈 **Marketing Campaigns** - Professional email marketing
- 🏢 **Business Outreach** - B2B communication campaigns
- 📧 **Newsletter Distribution** - Regular subscriber communications
- 🔔 **Notification Systems** - Automated system notifications
- 📊 **A/B Testing** - Campaign performance optimization

---

## ✨ **Key Features**

### 🚀 **Enterprise-Grade Performance**
- **Multi-threaded Processing** - Concurrent email sending across providers
- **Smart Queue Distribution** - Optimal load balancing algorithms
- **Rate Limiting Protection** - Prevent SMTP provider blocking
- **Failure Recovery** - Automatic sender failover and retry logic

### 📧 **Advanced Email Management**
- **Template Engine** - Dynamic HTML email generation
- **Personalization** - Custom field replacement and dynamic content
- **Attachment Support** - File attachments with CID embedding
- **Email Validation** - Syntax and deliverability checking

### 🛡️ **Reliability & Monitoring**
- **Comprehensive Logging** - Detailed audit trails and debugging
- **Progress Tracking** - Real-time campaign monitoring
- **Error Handling** - Graceful failure management
- **Resume Capability** - Continue interrupted campaigns

### 🔧 **Flexible Configuration**
- **Multiple SMTP Providers** - Gmail, Outlook, Yahoo, custom servers
- **Configurable Limits** - Customizable rate limits and batch sizes
- **Template Management** - Easy template customization
- **Sender Management** - Multiple sender account support

---

## 🏗️ **System Architecture**

```mermaid
graph TB
    A[📧 Email Campaign Manager] --> B[📋 Recipient Manager]
    A --> C[🎨 Email Composer]
    A --> D[📤 Sender Manager]
    
    B --> E[📊 Smart Queue Manager]
    C --> F[📝 Template Engine]
    D --> G[⚡ Rate Limiter]
    
    E --> H[🔄 Queue Workers]
    F --> I[📧 Email Tasks]
    G --> J[📤 SMTP Senders]
    
    H --> K[📊 Progress Tracking]
    I --> L[📧 Email Delivery]
    J --> M[📈 Success/Failure Tracking]
    
    K --> N[📋 Campaign Reports]
    L --> N
    M --> N
```

### 🔧 **Core Components:**

| Component | Purpose | Location |
|-----------|---------|----------|
| **Main Controller** | Campaign orchestration | [`main.py`](main.py) |
| **Queue Manager** | Smart email distribution | [`modules/queue/smart_queue_manager.py`](modules/queue/smart_queue_manager.py) |
| **Email Composer** | Template processing | [`modules/mailer/email_composer.py`](modules/mailer/email_composer.py) |
| **Sender Manager** | SMTP account management | [`modules/sender/sender_manager.py`](modules/sender/sender_manager.py) |
| **Rate Limiter** | Throttling control | [`modules/rate_limiter/rate_limiter.py`](modules/rate_limiter/rate_limiter.py) |
| **Config Loader** | Settings management | [`config/config_loader.py`](config/config_loader.py) |

---

## 🚀 **Quick Start**

### 📦 **1. Installation**

```bash
# Navigate to mail directory
cd mail/

# Install dependencies (if not already installed)
pip install -r requirements.txt  # If requirements file exists
```

### ⚙️ **2. Configuration Setup**

```bash
# Copy example configuration
cp config/config.example.ini config/config.ini

# Edit configuration with your settings
nano config/config.ini
```

**Essential configuration in [`config/config.ini`](config/config.ini):**

```ini
[SENDERS]
sender1_email = your-email@gmail.com
sender1_password = your-app-password
sender1_provider = gmail

[EMAIL_CONTENT]
subject = Your Campaign Subject
body_html_file = templates/email_templates/professional.html

[RECIPIENTS]
recipients_path = recipients.csv
```

### 📧 **3. Prepare Recipients**

Create [`recipients.csv`](recipients.csv) with your recipient list:
```csv
email,name,company
john@example.com,John Doe,TechCorp
jane@company.com,Jane Smith,BusinessInc
```

### 🚀 **4. Launch Campaign**

```bash
# Start email campaign
python main.py

# Monitor progress in real-time
tail -f logs/latest/all.log
```

---

## ⚙️ **Configuration Guide**

### 📁 **Configuration Files**
- **Main Config:** [`config/config.ini`](config/config.ini) - Your campaign settings
- **Example Config:** [`config/config.example.ini`](config/config.example.ini) - Complete reference

### 🔧 **Key Configuration Sections**

#### 📤 **SMTP Provider Setup**
```ini
[SMTP_CONFIGS]
# Gmail Configuration
gmail_host = smtp.gmail.com
gmail_port = 587
gmail_use_tls = True

# Outlook Configuration  
outlook_host = smtp.office365.com
outlook_port = 587
outlook_use_tls = True

# Custom SMTP
custom_host = smtp.yourprovider.com
custom_port = 587
custom_use_tls = True
```

#### 👤 **Sender Account Management**
```ini
[SENDERS]
sender1_email = marketing@company.com
sender1_password = app-specific-password
sender1_provider = gmail
sender1_daily_limit = 500

sender2_email = outreach@company.com  
sender2_password = app-specific-password
sender2_provider = outlook
sender2_daily_limit = 300
```

#### 📧 **Email Content Configuration**
```ini
[EMAIL_CONTENT]
subject = Professional Outreach - {{company}}
body_html_file = templates/email_templates/business_outreach.html
from_name = Your Name
reply_to = replies@company.com
```

#### ⚡ **Performance & Rate Limiting**
```ini
[RATE_LIMITING]
emails_per_minute = 30
emails_per_hour = 500
batch_size = 50
delay_between_batches = 60

[QUEUE_MANAGEMENT]
max_queue_size = 1000
rebalance_threshold = 0.3
```

### 📖 **Complete Configuration Reference**
See [`config/config.example.ini`](config/config.example.ini) for detailed documentation of all available options.

---

## 📊 **Usage Examples**

### 🎯 **Basic Email Campaign**

```bash
# Simple campaign with default settings
python main.py

# Campaign with custom batch size
python main.py --batch-size 25

# Resume interrupted campaign
python main.py --resume
```

### 📧 **Template Customization**

**Create custom template in [`templates/email_templates/`](templates/email_templates/):**

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{subject}}</title>
</head>
<body>
    <h1>Hello {{name}}!</h1>
    <p>We're reaching out to {{company}} regarding...</p>
    
    <!-- Dynamic content -->
    <p>Best regards,<br>{{sender_name}}</p>
</body>
</html>
```

**Configure template usage:**
```ini
[EMAIL_CONTENT]
body_html_file = templates/email_templates/custom_template.html
```

### 🔄 **Advanced Campaign Management**

**Multi-sender campaign:**
```ini
[SENDERS]
# Primary sender
sender1_email = primary@company.com
sender1_daily_limit = 500

# Backup sender  
sender2_email = backup@company.com
sender2_daily_limit = 300

# High-volume sender
sender3_email = bulk@company.com
sender3_daily_limit = 1000
```

**Smart queue distribution:**
```ini
[QUEUE_MANAGEMENT]
distribution_strategy = balanced  # balanced, weighted, priority
max_queue_size = 2000
rebalance_interval = 300
```

---

## 🔧 **Advanced Features**

### 📊 **Smart Queue Management**

The system automatically distributes emails across senders based on:
- **Current queue lengths** - Balance load evenly
- **Sender capacity** - Respect daily limits
- **Failure rates** - Avoid problematic senders
- **Rate limits** - Prevent provider blocking

### 🔄 **Intelligent Retry Logic**

**Automatic retry with exponential backoff:**
```python
# Retry configuration
max_retries = 3
base_delay = 60  # seconds
backoff_multiplier = 2

# Retry delays: 60s, 120s, 240s
```

### 📈 **Real-time Monitoring**

**Progress tracking includes:**
- ✅ **Emails sent successfully**
- ❌ **Failed deliveries**  
- ⏳ **Queue status**
- 📊 **Sender performance**
- ⚡ **Rate limit status**

### 🎨 **Template Personalization**

**Available variables:**
- `{{name}}` - Recipient name
- `{{email}}` - Recipient email
- `{{company}}` - Company name
- `{{sender_name}}` - Sender name
- `{{custom_field}}` - Any CSV column

### 📎 **Attachment Management**

```ini
[EMAIL_ATTACHMENTS]
# File attachments
resume = attachments/resume.pdf:resume_attachment
brochure = attachments/company_brochure.pdf:brochure

# Embedded images (CID)
logo = resume/company_logo.jpg:company_logo_cid
```

---

## 🛠️ **Troubleshooting**

### 🔧 **Common Issues**

**❌ "SMTP Authentication Failed"**
```bash
# For Gmail: Use App Passwords
# 1. Enable 2FA on your Google account
# 2. Generate App Password
# 3. Use App Password in config, not regular password
```

**❌ "Rate Limit Exceeded"**
```ini
# Reduce sending rate in config/config.ini
[RATE_LIMITING]
emails_per_minute = 10  # Reduce from default
delay_between_batches = 120  # Increase delay
```

**❌ "Template Not Found"**
```bash
# Ensure template file exists
ls templates/email_templates/
# Check file path in config
```

### 📊 **Performance Optimization**

**For high-volume campaigns:**
```ini
[PERFORMANCE]
max_workers = 10           # Increase concurrent workers
batch_size = 100          # Larger batches
queue_size = 5000         # Larger queue capacity

[RATE_LIMITING]
emails_per_minute = 100   # Higher rate (if provider allows)
```

**For reliability:**
```ini
[RELIABILITY]
max_retries = 5           # More retry attempts
retry_delay = 300         # Longer retry delays
failure_threshold = 0.1   # Lower failure tolerance
```

### 🔍 **Debugging**

```bash
# Enable debug logging
# In config/config.ini:
[LOGGING]
console_level = DEBUG
file_level = DEBUG

# Monitor specific components
tail -f logs/latest/sender.log
tail -f logs/latest/queue.log
tail -f logs/latest/rate_limiter.log
```

---

<div align="center">

**🌟 Professional Email Campaign Management Made Simple!**

*Built for reliability, scalability, and ease of use*

**[⬆️ Back to Top](#-professional-email-campaign-manager)**

</div>

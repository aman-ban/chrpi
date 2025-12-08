# ☀️ chrpi: A Positive Social Media Platform

**Domain:** chrpi.com

## Table of Contents

1.  [About chrpi](#about-chrpi)
2.  [Key Features](#key-features)
3.  [Technology Stack](#technology-stack)
4.  [Getting Started](#getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
5.  [Database Schema](#database-schema)
6.  [Development Notes](#development-notes)

---

## 1. About chrpi

**chrpi** is a Flask-based micro-social network dedicated exclusively to sharing **positive and uplifting content**. The name "chrpi" reflects the cheerful and lighthearted nature of the platform.

The core principle remains: **If a post doesn't meet a neutral or positive sentiment threshold, it doesn't get published.** This ensures every user's feed is a source of joy and optimism.

---

## 2. Key Features

* **Multi-Emoji Reactions (😊, 😂, 🥹):** Users can react to posts using a small selection of positive emojis, and the system tracks and displays the counts for each type of reaction.
* **Link Preview Scraping:** Posts containing external URLs automatically scrape the link's metadata (Open Graph tags) to display a relevant preview image if the user doesn't upload one.
* **Strict Sentiment Filtering:** Uses the `TextBlob` library to analyze post content and reject submissions that fall below a configured neutral/positive polarity threshold.
* **Personalized Feeds:** Users can view a chronological feed of posts only from followed users, or browse the Top 100 most-smiled posts globally.
* **Secure Authentication:** User registration and login utilize **Werkzeug security** for strong password hashing.
* **CSRF Protection:** Full Cross-Site Request Forgery protection on all mutating routes (`POST` requests) via `Flask-WTF`.

---

## 3. Technology Stack

* **Backend:** [Python 3.x]
* **Web Framework:** [Flask]
* **Database:** [SQLite3]
* **Security:** [Werkzeug] (Password Hashing) and [Flask-WTF] (CSRF Protection)
* **Sentiment Analysis:** [TextBlob] (Requires NLTK data to be downloaded)
* **Scraping:** [requests] and [BeautifulSoup4] (for link previews)
* **Front-end:** [Bootstrap 5.3] (for utility classes), [Custom CSS], [Jinja2] (Templating)

---

## 4. Getting Started

Follow these steps to get a local copy of the project up and running.

### Prerequisites

You will need the following installed:

* **Python 3.x**
* `pip` (Python package installer)
* A working virtual environment (`.venv`)

### Installation

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/your-username/chrpi-app.git](https://github.com/your-username/chrpi-app.git)
    cd chrpi-app
    ```

2.  **Activate Virtual Environment (Example for macOS/Linux):**
    ```bash
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    Assuming you have a `requirements.txt` file listing all libraries (`Flask`, `werkzeug`, `requests`, `textblob`, `python-dotenv`, etc.):
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download TextBlob Corpora:**
    This is required for the sentiment analysis to work:
    ```bash
    python -m textblob.download_corpora
    ```

5.  **Set Environment Variables:**
    Create a file named **`.env`** in the root directory and add your secret key. This file is excluded from Git by the `.gitignore` file.

    ```text
    # .env
    FLASK_SECRET_KEY="YOUR_LONG_RANDOM_STRING_HERE"
    ```

6.  **Run the Application:**
    The database (`chrpi.db`) will be initialized automatically on the first run.

    ```bash
    python main.py
    ```

The application should now be running at `http://127.0.0.1:5000/`.

---

## 5. Database Schema

The application uses an SQLite database (`chrpi.db`) with the following key tables:

| Table Name | Purpose | Key Columns |
| :--- | :--- | :--- |
| `users` | Stores user credentials and profile data. | `id`, `username`, `password`, `bio`, `profile_image` |
| `posts` | Stores all user-created content. | `id`, `user_id`, `content`, `image`, `link`, `smiles`, `timestamp` |
| **`post_smiles`** | **NEW:** Tracks which user reacted to which post and with which emoji. | `user_id`, `post_id`, **`reaction_emoji`** |
| `follows` | Tracks who follows whom. | `follower_id`, `followed_id` |

---

## 6. Development Notes

* **Database File:** The database file (`chrpi.db`) is ignored by Git, along with the virtual environment and the secret key file (`.env`).
* **CSRF:** All forms must include the hidden `csrf_token` input field to function.

---

Once you've saved this to your `README.md`, you can commit it:

```bash
git add README.md
git commit -m "CHORE: Update README.md with new name (chrpi) and features (multi-emoji, link scraping)."
git push origin main

# ☀️ chrpi: A Positive Social Media Platform

## Table of Contents

1.  [About chrpi](#about-chrpi)
2.  [Features](#features)
3.  [Color Palette](#color-palette)
4.  [Technology Stack](#technology-stack)
5.  [Getting Started](#getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
6.  [Database Schema](#database-schema)
7.  [Security and Sentiment Filtering](#security-and-sentiment-filtering)

---

## 1. About chrpi

chrpi is a Flask-based micro-social network dedicated exclusively to sharing positive and uplifting content. In a world saturated with negativity, BoonCheery filters out sad, angry, or pessimistic posts, ensuring a feed that only brings joy and optimism to its users.

The core principle is simple: **If it doesn't bring a smile, it doesn't get posted.**

---

## 2. Features

* **Positive Post Creation:** Users can share text, images, and external links, which are checked by a sentiment analyzer before publishing.
* **Sentiment Filtering:** Uses the `TextBlob` library to analyze post content and reject submissions that fall below a neutral/positive threshold.
* **Smile System:** A custom "smile" button allows users to show appreciation, replacing traditional 'likes' or 'hearts'.
* **Following Feed:** A personalized feed showing posts only from followed users.
* **Top Smiles Feed:** A chronological list of the top 100 most-smiled posts.
* **Secure Authentication:** User registration and login using Werkzeug security for password hashing.
* **CSRF Protection:** Full Cross-Site Request Forgery protection on all mutating routes (POST requests).

---

## 3. Color Palette

chrpi uses a cheerful and optimistic palette:

| Color Name | Hex Code | Usage |
| :--- | :--- | :--- |
| **Soft Apricot** | `#fed9b7ff` | Primary Background |
| **Cerulean** | `#0081a7ff` | Main Text, Primary CTA (Buttons) |
| **Tropical Teal** | `#00afb9ff` | Navbar Background, Hover States |
| **Vibrant Coral** | `#f07167ff` | "Smile" Button, Accents |
| **Light Yellow** | `#fdfcdcff` | Card Borders, Metadata Background |

---

## 4. Technology Stack

* **Backend:** [Python 3.x]
* **Web Framework:** [Flask]
* **Database:** [SQLite3]
* **Security:** [Werkzeug] (Password Hashing) and [Flask-WTF] (CSRF Protection)
* **Sentiment Analysis:** [TextBlob]
* **Front-end:** [Bootstrap 5.3] (for utility classes), [Custom CSS], [Jinja2] (Templating)

---

## 5. Getting Started

Follow these steps to get a local copy of the project up and running.

### Prerequisites

You will need the following installed:

* Python 3.x
* `pip` (Python package installer)

### Installation

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/your-username/BoonCheery-App.git](https://github.com/your-username/BoonCheery-App.git)
    cd chrpi-App
    ```

2.  **Create and Activate Virtual Environment:**
    * *macOS/Linux:*
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```
    * *Windows:*
        ```bash
        python -m venv .venv
        .venv\Scripts\activate
        ```

3.  **Install Dependencies:**
    You must create a `requirements.txt` file listing all required libraries (`pip freeze > requirements.txt` if you know how, or list them manually: `Flask`, `werkzeug`, `sqlite3`, `Pillow`, `TextBlob`, `Flask-WTF`, `python-dotenv`).

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Environment Variables:**
    Create a file named `.env` in the root directory and add your secret key:

    ```text
    # .env
    FLASK_SECRET_KEY="YOUR_LONG_RANDOM_STRING"
    ```

5.  **Run the Application:**
    The database will be initialized automatically on the first run.

    ```bash
    python main.py
    ```

The application should now be running at `http://127.0.0.1:5000/`.

---

## 6. Database Schema

The application uses an SQLite database (`booncheery.db`) with the following tables:

| Table Name | Purpose | Key Columns |
| :--- | :--- | :--- |
| `users` | Stores user credentials and profile data. | `id`, `username`, `password`, `bio`, `profile_image` |
| `posts` | Stores all user-created content. | `id`, `user_id`, `content`, `image`, `link`, `smiles`, `timestamp` |
| `follows` | Tracks who follows whom. | `follower_id`, `followed_id` |
| `post_smiles` | Tracks which user has smiled at which post (unique constraint). | `user_id`, `post_id` |

---

## 7. Security and Sentiment Filtering

chrpi enforces positivity using:

* **Sentiment Analysis:** The `create_post` route utilizes `TextBlob` to check if the post's polarity is `>= -0.1` (neutral or positive) before allowing submission.
* **CSRF Protection:** Implemented using `Flask-WTF` to secure all POST requests.
* **Safe Redirects:** Implements URL parsing checks to prevent open redirect vulnerabilities.
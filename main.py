import os
import sqlite3
import uuid
import random
from flask import Flask, render_template, request, redirect, session, g, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, urljoin  # <--- FIXED IMPORT
from PIL import Image
from textblob import TextBlob
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()

# --- Config ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_DIR, "static", "uploads")
DB_PATH = os.path.join(APP_DIR, "booncheery.db")
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "amhdnrba!102998")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize CSRF Protection
csrf = CSRFProtect(app)


# --- DB helpers ---
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_database", None)
    if db:
        db.close()


def init_db():
    db = get_db()

    # Users Table
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        bio TEXT DEFAULT '',
        profile_image TEXT DEFAULT ''
    );
    """)

    # Posts Table
    db.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT NOT NULL,
        image TEXT DEFAULT '',
        link TEXT DEFAULT '',
        smiles INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # Follows Table
    db.execute("""
    CREATE TABLE IF NOT EXISTS follows (
        follower_id INTEGER,
        followed_id INTEGER,
        UNIQUE (follower_id, followed_id)
    );
    """)

    # Post Smiles Table
    db.execute("""
    CREATE TABLE IF NOT EXISTS post_smiles (
        user_id INTEGER,
        post_id INTEGER,
        reaction_emoji TEXT DEFAULT '😊', -- NEW: Store the specific emoji here
        UNIQUE (user_id, post_id)
    );
    """)
    db.commit()


# --- Auth & Utility helpers ---
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def save_image(file_storage, resize_to=900):
    if not file_storage or file_storage.filename == "":
        return ""
    if not allowed_file(file_storage.filename):
        return ""
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    new_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], new_name)
    file_storage.save(path)
    try:
        img = Image.open(path)
        img.thumbnail((resize_to, resize_to))
        img.save(path)
    except Exception:
        pass
    return f"/static/uploads/{new_name}"


def analyze_sentiment(text: str):
    """
    Returns True if sentiment is positive or neutral.
    Returns False if sentiment is negative.
    """
    if not text:
        return True

    analysis = TextBlob(text)
    print(f"DEBUG: Text: '{text}' | Polarity: {analysis.sentiment.polarity}")

    return analysis.sentiment.polarity >= -0.1


def get_safe_redirect(target):
    """Ensures we don't redirect users to external phishing sites."""
    if not target:
        return url_for('feed')
    target_url = urlparse(target)  # <--- FIXED USAGE
    if target_url.netloc != '' and target_url.netloc != request.host:
        return url_for('feed')
    return target


def get_link_preview_image(url: str):
    """Fetches the og:image URL from an external link's metadata."""
    if not url:
        return ""

    try:
        # Use a user-agent to avoid being blocked by some sites
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()  # Raise exception for bad status codes

        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. Look for the og:image tag (standard for social media previews)
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            image_url = og_image.get("content")

            # CRITICAL: Ensure the URL is absolute before saving.
            # If it's relative (e.g., /images/preview.jpg), join it with the base URL.
            return urljoin(url, image_url)

        # 2. Fallback: Look for a standard favicon or first image
        favicon = soup.find("link", rel="icon")
        if favicon and favicon.get("href"):
            return urljoin(url, favicon.get("href"))

    except Exception as e:
        print(f"DEBUG: Failed to get link preview for {url}. Error: {e}")
        return ""
    return ""

# --- Routes ---
@app.before_request
def before_request():
    init_db()


@app.route("/")
def index():
    return render_template("index.html", user=current_user())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        a, b = random.randint(1, 9), random.randint(1, 9)
        session["captcha_answer"] = str(a + b)
        return render_template("register.html", a=a, b=b, user=current_user())

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    captcha = request.form.get("captcha", "")

    if not username or not password:
        flash("Please provide username and password.")
        return redirect("/register")

    if captcha != session.get("captcha_answer"):
        flash("Math captcha incorrect.")
        return redirect("/register")

    db = get_db()
    try:
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                   (username, generate_password_hash(password)))
        db.commit()
        flash("Registered — please log in.")
        return redirect("/login")
    except sqlite3.IntegrityError:
        flash("Username already taken.")
        return redirect("/register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", user=current_user())

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        flash("Logged in.")
        return redirect("/feed")

    flash("Invalid credentials.")
    return redirect("/login")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.")
    return redirect("/")


@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():
    user = current_user()
    if not user:
        return redirect("/login")

    if request.method == "POST":
        bio = request.form.get("bio", "")
        image = request.files.get("image")
        filename = user["profile_image"]

        if image and image.filename:
            saved = save_image(image, resize_to=400)
            if saved:
                filename = saved

        db = get_db()
        db.execute("UPDATE users SET bio = ?, profile_image = ? WHERE id = ?",
                   (bio, filename, user["id"]))
        db.commit()
        flash("Profile updated.")
        return redirect(url_for("user_profile", username=user["username"]))

    return render_template("edit_profile.html", user=user)


@app.route("/user/<username>")
def user_profile(username):
    db = get_db()
    profile = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not profile:
        return "User not found", 404

    me = current_user()
    is_following = False
    if me:
        q = db.execute("SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?",
                       (me["id"], profile["id"])).fetchone()
        is_following = bool(q)

    posts = db.execute("SELECT * FROM posts WHERE user_id = ? ORDER BY timestamp DESC", (profile["id"],)).fetchall()

    return render_template("profile.html", profile=profile, posts=posts, user=me, is_following=is_following)


@app.route("/follow/<int:user_id>", methods=["POST"])
def follow(user_id):
    me = current_user()
    if not me:
        return redirect("/login")

    db = get_db()
    db.execute("INSERT OR IGNORE INTO follows (follower_id, followed_id) VALUES (?, ?)",
               (me["id"], user_id))
    db.commit()

    return redirect(get_safe_redirect(request.referrer))


@app.route("/unfollow/<int:user_id>", methods=["POST"])
def unfollow(user_id):
    me = current_user()
    if not me:
        return redirect("/login")

    db = get_db()
    db.execute("DELETE FROM follows WHERE follower_id = ? AND followed_id = ?",
               (me["id"], user_id))
    db.commit()

    return redirect(get_safe_redirect(request.referrer))


@app.route("/post", methods=["GET", "POST"])
def create_post():
    me = current_user()
    if not me:
        return redirect("/login")

    if request.method == "GET":
        # NEW: Use the distinct template name 'post_form.html'
        return render_template("post_form.html", user=me)

    content = request.form.get("content", "").strip()
    link = request.form.get("link", "").strip()
    image_file = request.files.get("image")

    has_image = image_file and image_file.filename
    if not content and not link and not has_image:
        flash("Please include something in your post (content, link, or image).")
        return redirect("/post")

    if content:
        if not analyze_sentiment(content):
            flash("That post seems a bit negative. Let's keep it uplifting!")
            return redirect("/post")

    image_path = ""

    # 1. Check for user-uploaded image first
    if has_image:
        image_path = save_image(image_file)

    # 2. If no user image AND a link is present, scrape the link for a preview image
    elif link:
        # We don't save the remote image locally, we save the remote URL directly to the database
        image_path = get_link_preview_image(link)


    db = get_db()
    db.execute(
        "INSERT INTO posts (user_id, content, image, link) VALUES (?, ?, ?, ?)",
        (me["id"], content, image_path, link)
    )
    db.commit()

    flash("Your post has been shared!")
    return redirect(url_for('feed'))


@app.route('/smile/<int:post_id>', methods=['POST'])
def smile(post_id):
    me = current_user()
    if not me:
        return redirect(url_for('login'))

    # NEW: Get the reaction from the form submission (default to a smile)
    reaction = request.form.get("reaction", "😊")

    db = get_db()

    # Check if the user has already reacted to this post
    existing = db.execute("SELECT 1 FROM post_smiles WHERE user_id = ? AND post_id = ?",
                          (me["id"], post_id)).fetchone()

    # Define a set of allowed emojis
    ALLOWED_EMOJIS = {"😊", "😂", "🥹"}

    if reaction not in ALLOWED_EMOJIS:
        # Default to the standard smile if an invalid emoji is sent
        reaction = "😊"

    if not existing:
        # If no existing smile, insert the new reaction and increment total smiles
        db.execute("INSERT INTO post_smiles (user_id, post_id, reaction_emoji) VALUES (?, ?, ?)",
                   (me["id"], post_id, reaction))
        db.execute("UPDATE posts SET smiles = smiles + 1 WHERE id = ?", (post_id,))
        db.commit()
    else:
        # User already reacted. If they click a different button, update the reaction
        # but DON'T change the smiles count (since it's a unique reaction per user).
        # We could also use this logic to allow the user to 'un-smile' if the reaction
        # is the same, but for simplicity, let's allow them to change the type of smile.
        db.execute("UPDATE post_smiles SET reaction_emoji = ? WHERE user_id = ? AND post_id = ?",
                   (reaction, me["id"], post_id))
        db.commit()

    return redirect(get_safe_redirect(request.referrer))


@app.route("/feed")
def feed():
    me = current_user()
    if not me:
        return redirect("/login")
    db = get_db()

    posts = db.execute("""
        SELECT 
            posts.*, 
            users.username, 
            users.profile_image,
            -- Get the user's specific reaction if it exists
            (SELECT reaction_emoji FROM post_smiles WHERE post_smiles.post_id = posts.id AND post_smiles.user_id = ?) as user_reaction,
            -- Get the top 3 most common reactions and their counts for display
            (SELECT GROUP_CONCAT(reaction_emoji || ':' || reaction_count) 
             FROM (SELECT reaction_emoji, COUNT(*) as reaction_count 
                   FROM post_smiles 
                   WHERE post_id = posts.id 
                   GROUP BY reaction_emoji 
                   ORDER BY reaction_count DESC 
                   LIMIT 3)
            ) as top_reactions
        FROM posts
        JOIN users ON posts.user_id = users.id
        JOIN follows ON posts.user_id = follows.followed_id
        WHERE follows.follower_id = ?
        ORDER BY posts.timestamp DESC
    """, (me["id"], me["id"])).fetchall()

    return render_template("feed.html", posts=posts, user=me, title="Following Feed")


@app.route("/top")
def top():
    user = current_user()
    user_id = user["id"] if user else 0
    db = get_db()

    posts = db.execute("""
        SELECT 
            posts.*, 
            users.username, 
            users.profile_image,
            -- Get the user's specific reaction if it exists
            (SELECT reaction_emoji FROM post_smiles WHERE post_smiles.post_id = posts.id AND post_smiles.user_id = ?) as user_reaction,
            -- Get the top 3 most common reactions and their counts for display
            (SELECT GROUP_CONCAT(reaction_emoji || ':' || reaction_count) 
             FROM (SELECT reaction_emoji, COUNT(*) as reaction_count 
                   FROM post_smiles 
                   WHERE post_id = posts.id 
                   GROUP BY reaction_emoji 
                   ORDER BY reaction_count DESC 
                   LIMIT 3)
            ) as top_reactions
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.smiles DESC, posts.timestamp DESC
        LIMIT 100
    """, (user_id,)).fetchall()

    return render_template("feed.html", posts=posts, user=user, title="Top Smiled Posts")


@app.route('/view/<int:post_id>')
def view_single_post(post_id):
    me = current_user()
    db = get_db()

    # Use a SQL query to fetch the single post, joining user info and smile status
    post = db.execute("""
        SELECT 
            posts.*, 
            users.username, 
            users.profile_image,
            -- Get the user's specific reaction if it exists
            (SELECT reaction_emoji FROM post_smiles WHERE post_smiles.post_id = posts.id AND post_smiles.user_id = ?) as user_reaction,
            -- Get the top 3 most common reactions and their counts for display
            (SELECT GROUP_CONCAT(reaction_emoji || ':' || reaction_count) 
             FROM (SELECT reaction_emoji, COUNT(*) as reaction_count 
                   FROM post_smiles 
                   WHERE post_id = posts.id 
                   GROUP BY reaction_emoji 
                   ORDER BY reaction_count DESC 
                   LIMIT 3)
            ) as top_reactions
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.id = ?
    """, (me["id"] if me else 0, post_id)).fetchone()

    if not post:
        return "Post not found", 404

    # We will rename the template to 'post_view.html' in the next step
    return render_template('post_view.html', post=post, user=me, title=f"Post by {post['username']}")

# --- Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    # Renders a 404.html template and sends a 404 HTTP status code
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # Renders a 500.html template and sends a 500 HTTP status code
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=True)
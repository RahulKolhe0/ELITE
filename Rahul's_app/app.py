from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database setup
os.makedirs("database", exist_ok=True)
DB_PATH = 'database/users.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # USERS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # POSTS (added views column)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # LIKES (for posts)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (post_id) REFERENCES posts(id),
                UNIQUE(user_id, post_id)
            )
        ''')

        # COMMENTS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        ''')

        # comment_likes (for comment popularity)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comment_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                comment_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (comment_id) REFERENCES comments(id),
                UNIQUE(user_id, comment_id)
            )
        ''')

        # BOOKMARKS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (post_id) REFERENCES posts(id),
                UNIQUE(user_id, post_id)
            )
        ''')

        # SHARES (simple record)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        ''')

        conn.commit()
init_db()


# Home
@app.route('/')
def home():
    return render_template('index.html')


# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()

        if not username or not email or not password:
            flash("All fields are required!")
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('signup'))

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user_by_username = cursor.fetchone()

            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user_by_email = cursor.fetchone()

            if user_by_username and user_by_email:
                flash("User already exists with this username and email!")
                return redirect(url_for('signup'))
            elif user_by_username:
                flash("Username already taken!")
                return redirect(url_for('signup'))
            elif user_by_email:
                flash("An account already exists with this email!")
                return redirect(url_for('signup'))

            hashed_pw = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                           (username, email, hashed_pw))
            conn.commit()

        flash("Signup successful! Please log in.")
        return redirect(url_for('login'))

    return render_template('signup.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()

        if result and check_password_hash(result[0], password):
            session["username"] = username
            return redirect(url_for('main_page'))
        else:
            flash("Wrong username or password!")
            return redirect(url_for('login'))

    return render_template('login.html')


# Logout
@app.route('/logout')
def logout():
    session.pop("username", None)
    flash("You have been logged out.")
    return redirect(url_for('login'))


# Create Post
@app.route('/post', methods=['POST'])
def create_post():
    if "username" not in session:
        flash("Please login first!")
        return redirect(url_for('login'))

    content = request.form.get("content", "").strip()
    if not content:
        flash("Post cannot be empty!")
        return redirect(url_for('main_page'))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (session["username"],))
        user = cursor.fetchone()
        if user:
            cursor.execute("INSERT INTO posts (user_id, content) VALUES (?, ?)", (user[0], content))
            conn.commit()

    flash("Post created successfully!")
    return redirect(url_for('main_page'))


# Like Post
@app.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    if "username" not in session:
        return redirect(url_for("login"))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=?", (session["username"],))
        user_id = cursor.fetchone()[0]

        # check if already liked
        cursor.execute("SELECT id FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        existing_like = cursor.fetchone()

        if existing_like:
            # unlike (remove row)
            cursor.execute("DELETE FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        else:
            # like (insert row)
            cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))

        conn.commit()

    return redirect(request.referrer or url_for("main_page"))

# Add Comment
@app.route("/add_comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    if "username" not in session:
        return redirect(url_for("login"))

    comment_text = request.form.get("comment", "").strip()
    if not comment_text:
        return redirect(url_for("main_page"))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=?", (session["username"],))
        user_id = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO comments (user_id, post_id, comment) VALUES (?, ?, ?)",
            (user_id, post_id, comment_text),
        )
        conn.commit()

    return redirect(request.referrer or url_for("main_page"))

# Bookmark Post
@app.route('/bookmark/<int:post_id>', methods=['POST'])
def bookmark_post(post_id):
    if "username" not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=?", (session["username"],))
        user_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO bookmarks (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.commit()
    flash("Post bookmarked!")
    return redirect(url_for('main_page'))


# Share Post
@app.route('/share/<int:post_id>', methods=['POST'])
def share_post(post_id):
    flash("You can copy and share this post link!")
    return redirect(url_for('main_page'))


# Main Feed
@app.route('/main')
def main_page():
    if "username" not in session:
        flash("Please login first!")
        return redirect(url_for('login'))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT posts.id, posts.content, posts.created_at, users.username
            FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY posts.created_at DESC
        ''')
        posts = cursor.fetchall()

        post_data = []
        for post in posts:
            post_id = post[0]
            cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
            like_count = cursor.fetchone()[0]

            cursor.execute('''
                SELECT users.username, comments.comment
                FROM comments
                JOIN users ON comments.user_id = users.id
                WHERE comments.post_id=?
                ORDER BY comments.created_at DESC
                LIMIT 5
            ''', (post_id,))
            comments = cursor.fetchall()

            post_data.append({
                "id": post_id,
                "content": post[1],
                "created_at": post[2],
                "username": post[3],
                "likes": like_count,
                "comments": comments
            })

    return render_template('main.html', username=session["username"], posts=post_data)

# Post detail view (single post / dropdown panel)
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    if "username" not in session:
        flash("Please login first!")
        return redirect(url_for('login'))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # increase view count
        cursor.execute("UPDATE posts SET views = views + 1 WHERE id = ?", (post_id,))
        conn.commit()

        # Post info
        cursor.execute('''
            SELECT posts.id, posts.content, posts.created_at, posts.views, users.username
            FROM posts
            JOIN users ON posts.user_id = users.id
            WHERE posts.id = ?
        ''', (post_id,))
        post = cursor.fetchone()
        if not post:
            flash("Post not found.")
            return redirect(url_for('main_page'))

        # likes count for post
        cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,))
        likes = cursor.fetchone()[0]

        # top 5 comments by number of likes (popularity), tie-breaker: newest
        cursor.execute('''
            SELECT c.id, u.username, c.comment, c.created_at,
                   COUNT(cl.id) as likes
            FROM comments c
            JOIN users u ON c.user_id = u.id
            LEFT JOIN comment_likes cl ON cl.comment_id = c.id
            WHERE c.post_id = ?
            GROUP BY c.id
            ORDER BY likes DESC, c.created_at DESC
            LIMIT 5
        ''', (post_id,))
        top_comments = cursor.fetchall()

        # count of remaining comments
        cursor.execute("SELECT COUNT(*) FROM comments WHERE post_id = ?", (post_id,))
        total_comments = cursor.fetchone()[0]
        remaining = max(0, total_comments - len(top_comments))

    return render_template('post_detail.html',
                           post={"id": post[0], "content": post[1], "created_at": post[2], "views": post[3], "username": post[4]},
                           likes=likes,
                           top_comments=top_comments,
                           remaining=remaining)

# Like a comment
@app.route('/comment_like/<int:comment_id>', methods=['POST'])
def comment_like(comment_id):
    if "username" not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=?", (session["username"],))
        user_id = cursor.fetchone()[0]
        try:
            cursor.execute("INSERT INTO comment_likes (user_id, comment_id) VALUES (?, ?)", (user_id, comment_id))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
    return redirect(request.referrer or url_for('main_page'))

# Fetch rest comments (simple page)
@app.route('/post/<int:post_id>/comments')
def post_comments(post_id):
    if "username" not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, u.username, c.comment, c.created_at,
                   (SELECT COUNT(*) FROM comment_likes cl WHERE cl.comment_id = c.id) as likes
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at DESC
        ''', (post_id,))
        comments = cursor.fetchall()
    return render_template('post_comments.html', comments=comments, post_id=post_id)


if __name__ == '__main__':
    app.run(debug=True)

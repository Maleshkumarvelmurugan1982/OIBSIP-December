from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import json, os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "02b5c839e30f13004c70ad95c7860eb611b1ec93ada31f09dd89dc4922211406"

USERS_FILE = "users.json"
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------
# JSON Load/Save
# ---------------------------------------------------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

users_db = load_users()

# ---------------------------------------------------------
# HTML Layout
# ---------------------------------------------------------
layout = """
<!doctype html>
<title>{{title}}</title>
<style>
body { font-family: Segoe UI, Arial; background: #FCE9F1; padding: 40px; }
.container { background: #fff; border-radius: 12px; max-width: 430px; margin: auto; box-shadow: 0 8px 32px #efb2fa7a; padding: 32px; }
input, button { font-size: 1.05em; padding: 8px 11px; margin:6px 0; width:98%; border-radius:6px; border:1px solid #c7c7e2; }
button { background: linear-gradient(120deg,#fe85d3 70%, #8afdc8 100%); color:#333;}
a {color:#fe85d3;text-decoration:none;}
.msg {color:#d80073;}
.secured {color:#298671; font-weight:bold; margin:17px 0;}
img {max-width:100%; border-radius:10px; margin:10px 0;}
</style>
<div class="container">
    <h2 style="text-align:center;color:#fe85d3;">{{title}}</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="msg">{% for msg in messages %}{{msg}}<br>{% endfor %}</div>
      {% endif %}
    {% endwith %}
    {{body|safe}}
</div>
"""

def render(title, body):
    return render_template_string(layout, title=title, body=body)

# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------
@app.route('/')
def home():
    if 'user' in session:
        u = session['user']
        body = f"""
        <p>Welcome <b>{u}</b>!</p>
        <p><a href="{url_for('secured')}">Your Profile</a></p>
        <p><a href="{url_for('edit_profile')}">Edit Profile</a></p>
        <form method="POST" action="{url_for('logout')}">
            <button>Logout</button>
        </form>
        """
    else:
        body = f"""
        <p><a href="{url_for('login')}">Login</a> or 
        <a href="{url_for('register')}">Register</a></p>
        """
    return render("Home", body)

# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    body = f"""
    <form method="POST" enctype="multipart/form-data">

        <input name="username" placeholder="Username" required>

        <input type="password" name="password" placeholder="Password" required>
        <input type="password" name="confirm_password" placeholder="Confirm Password" required>

        <input name="full_name" placeholder="Full Name" required>
        <input name="email" placeholder="Email" required>
        <input name="phone" placeholder="Phone" required>
        <input name="address" placeholder="Address" required>
        <input name="city" placeholder="City" required>
        <input name="country" placeholder="Country" required>
        <input name="age" placeholder="Age" required>

        <label>Upload Profile Photo:</label>
        <input type="file" name="photo">

        <button type="submit">Register</button>
    </form>
    <p>Already have an account? <a href="{url_for('login')}">Login here</a></p>
    """

    if request.method == 'POST':
        uname = request.form['username']
        pw = request.form['password']
        cpw = request.form['confirm_password']

        if uname in users_db:
            flash("Username already exists.")
            return render("Register", body)

        if pw != cpw:
            flash("Passwords do not match.")
            return render("Register", body)

        # Save Profile Photo
        photo_file = request.files.get("photo")
        filename = None

        if photo_file and photo_file.filename:
            filename = secure_filename(uname + "_" + photo_file.filename)
            photo_file.save(os.path.join(UPLOAD_FOLDER, filename))

        users_db[uname] = {
            "password": generate_password_hash(pw),
            "full_name": request.form['full_name'],
            "email": request.form['email'],
            "phone": request.form['phone'],
            "address": request.form['address'],
            "city": request.form['city'],
            "country": request.form['country'],
            "age": request.form['age'],
            "photo": filename
        }

        save_users(users_db)
        flash("Registered successfully!")
        return redirect(url_for('login'))

    return render("Register", body)

# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    body = f"""
    <form method="POST">
        <input name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button>Login</button>
    </form>
    <p><a href="{url_for('register')}">Create account</a></p>
    """

    if request.method == 'POST':
        uname = request.form['username']
        pw = request.form['password']

        user = users_db.get(uname)
        if not user or not check_password_hash(user['password'], pw):
            flash("Invalid username or password.")
            return render("Login", body)

        session['user'] = uname
        flash("Logged in!")
        return redirect(url_for('secured'))

    return render("Login", body)

# ---------------------------------------------------------
# PROFILE PAGE
# ---------------------------------------------------------
@app.route('/secured')
def secured():
    if "user" not in session:
        return redirect(url_for("login"))

    u = session['user']
    user = users_db[u]

    photo = user["photo"]
    photo_html = f'<img src="/static/uploads/{photo}">' if photo else "<p>No photo uploaded</p>"

    body = f"""
    <div class="secured">Your Profile</div>

    {photo_html}

    <p><b>Full Name:</b> {user['full_name']}</p>
    <p><b>Email:</b> {user['email']}</p>
    <p><b>Phone:</b> {user['phone']}</p>
    <p><b>Address:</b> {user['address']}</p>
    <p><b>City:</b> {user['city']}</p>
    <p><b>Country:</b> {user['country']}</p>
    <p><b>Age:</b> {user['age']}</p>

    <p><a href="{url_for('edit_profile')}">Edit Profile</a></p>
    <p><a href="{url_for('home')}">Home</a></p>
    """

    return render("Profile", body)

# ---------------------------------------------------------
# EDIT PROFILE
# ---------------------------------------------------------
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if "user" not in session:
        return redirect(url_for("login"))

    u = session['user']
    user = users_db[u]

    body = f"""
    <form method="POST" enctype="multipart/form-data">

        <input name="full_name" value="{user['full_name']}" required>
        <input name="email" value="{user['email']}" required>
        <input name="phone" value="{user['phone']}" required>
        <input name="address" value="{user['address']}" required>
        <input name="city" value="{user['city']}" required>
        <input name="country" value="{user['country']}" required>
        <input name="age" value="{user['age']}" required>

        <label>Change Photo:</label>
        <input type="file" name="photo">

        <button>Save Changes</button>
    </form>
    """

    if request.method == 'POST':
        user['full_name'] = request.form['full_name']
        user['email'] = request.form['email']
        user['phone'] = request.form['phone']
        user['address'] = request.form['address']
        user['city'] = request.form['city']
        user['country'] = request.form['country']
        user['age'] = request.form['age']

        # Handle new photo upload
        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            filename = secure_filename(u + "_" + photo_file.filename)
            photo_file.save(os.path.join(UPLOAD_FOLDER, filename))
            user['photo'] = filename

        save_users(users_db)
        flash("Profile updated!")
        return redirect(url_for("secured"))

    return render("Edit Profile", body)

# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@app.route('/logout', methods=['POST'])
def logout():
    session.pop("user", None)
    flash("Logged out!")
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True)


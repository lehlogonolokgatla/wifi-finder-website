import os
import random
from flask import Flask, jsonify, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, func
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# --- UPLOAD CONFIGURATION ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# --- DB CONFIGURATION ---
class Base(DeclarativeBase):
    pass


# Ensure this path is correct relative to main.py or if it's in the instance folder
# Using os.path.join and os.path.abspath is generally safer for robust path handling
# If your cafes.db is directly in the project root:
DB_FILE_PATH = 'sqlite:///cafes.db'
# If your cafes.db is in the 'instance' folder (recommended Flask default):
# DB_FILE_PATH = 'sqlite:///' + os.path.join(app.instance_path, 'cafes.db')

app.config['SQLALCHEMY_DATABASE_URI'] = DB_FILE_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(model_class=Base)
db.init_app(app)

print(f"DEBUG: SQLAlchemy is attempting to connect to database at: {app.config['SQLALCHEMY_DATABASE_URI']}")
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
    # For SQLite, convert to an absolute path for better debugging
    db_abs_path = os.path.abspath(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    print(f"DEBUG: Absolute path to SQLite DB file: {db_abs_path}")
    if not os.path.exists(db_abs_path):
        print(
            f"WARNING: Database file does NOT exist at {db_abs_path}. It might be created on first write, or path is wrong.")


# Cafe TABLE Configuration (Matching your provided schema)
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)
        return dictionary


with app.app_context():
    db.create_all()
    print("DEBUG: db.create_all() has been executed. Tables exist or were created.")


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- ROUTES ---

@app.route("/")
def home():
    """Renders the home page with all cafes."""
    with app.app_context():
        all_cafes = db.session.execute(db.select(Cafe)).scalars().all()

    print(f"DEBUG: Found {len(all_cafes)} cafes in the database for home page.")
    if all_cafes:
        print("DEBUG: Details of cafes fetched for home page:")
        for cafe in all_cafes:
            print(
                f"  - ID: {cafe.id}, Name: {cafe.name}, Location: {cafe.location}, Img_URL: {cafe.img_url}, Has_Wifi: {cafe.has_wifi}, Has_Sockets: {cafe.has_sockets}")
    else:
        print("DEBUG: No cafes found in the database.")

    return render_template("index.html", cafes=all_cafes, search_query=None, error_message=None)


@app.route("/add-cafe-form")
def add_cafe_form():
    return render_template("add_cafe.html")


@app.route("/search", methods=["GET"])
def search_cafes_by_location():
    location_query = request.args.get("loc")

    print(f"\nDEBUG: Search query received from browser: '{location_query}'")

    with app.app_context():
        if location_query:
            # Strip whitespace and convert to lowercase for the search term
            search_term_processed = location_query.strip().lower()
            sql_like_term = f"%{search_term_processed}%"
            print(f"DEBUG: Processed search term for SQL (with wildcards): '{sql_like_term}'")

            # Query for cafes where the lowercase location contains the search term
            query = db.select(Cafe).where(func.lower(Cafe.location).like(sql_like_term))

            # --- CRITICAL DEBUGGING STEP ---
            # Compile the query to see the raw SQL string and its parameters
            compiled_query = query.compile(db.engine)
            print(f"DEBUG: Compiled SQL Query for search: {compiled_query.string}")
            print(f"DEBUG: SQL Query Parameters: {compiled_query.params}")
            # --- END CRITICAL DEBUGGING STEP ---

            cafes_at_location = db.session.execute(query).scalars().all()
        else:  # If search query is empty, show all cafes (though this route is for search)
            cafes_at_location = db.session.execute(db.select(Cafe)).scalars().all()

        print(f"DEBUG: Number of cafes found by search: {len(cafes_at_location)}")
        if not cafes_at_location and location_query:
            print(f"DEBUG: No cafes found for query '{location_query}'.")
        elif cafes_at_location:
            print("DEBUG: Found cafes by search:")
            for cafe in cafes_at_location:
                print(f"  - {cafe.name} (Location: '{cafe.location}')")

        if cafes_at_location:
            return render_template("index.html", cafes=cafes_at_location, search_query=location_query,
                                   error_message=None)
        else:
            return render_template("index.html", cafes=[], search_query=location_query,
                                   error_message=f"No cafes found in '{location_query}'.")


@app.route("/add", methods=["POST"])
def add_new_cafe():
    img_filename = ""
    if 'img_file' in request.files:
        file = request.files['img_file']
        if file.filename == '':
            img_filename = "default.png"
            print("DEBUG: No image file selected, using default.png")
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = str(random.randint(10000, 99999)) + "_" + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            try:
                file.save(file_path)
                img_filename = unique_filename
                print(f"DEBUG: Image saved successfully: {file_path}")
            except Exception as e:
                print(f"ERROR: Failed to save image file: {e}")
                return render_template("add_cafe.html", error="Failed to save image file. Please try again."), 500
        else:
            print(f"ERROR: Invalid image file type or size: {file.filename}")
            return render_template("add_cafe.html",
                                   error="Invalid image file type (allowed: png, jpg, jpeg, gif) or file too large."), 400
    else:
        print(
            "ERROR: 'img_file' not in request.files. This usually means the form input name is incorrect or no file was uploaded.")
        return render_template("add_cafe.html",
                               error="No image file provided for upload. Ensure form input name is 'img_file'."), 400

    name = request.form.get("name")
    map_url = request.form.get("map_url")
    location = request.form.get("location").strip() if request.form.get("location") else ""
    seats = request.form.get("seats")
    coffee_price = request.form.get("coffee_price")

    has_toilet = bool(request.form.get("has_toilet"))
    has_wifi = bool(request.form.get("has_wifi"))
    has_sockets = bool(request.form.get("has_sockets"))
    can_take_calls = bool(request.form.get("can_take_calls"))

    print(f"\nDEBUG: Attempting to add new cafe with details:")
    print(f"  Name: '{name}'")
    print(f"  Map URL: '{map_url}'")
    print(f"  Image Filename: '{img_filename}'")
    print(f"  Location: '{location}'")
    print(f"  Seats: '{seats}'")
    print(f"  Toilet: {has_toilet}, Wifi: {has_wifi}, Sockets: {has_sockets}, Calls: {can_take_calls}")
    print(f"  Coffee Price: '{coffee_price}'")

    try:
        new_cafe = Cafe(
            name=name,
            map_url=map_url,
            img_url=img_filename,
            location=location,
            seats=seats,
            has_toilet=has_toilet,
            has_wifi=has_wifi,
            has_sockets=has_sockets,
            can_take_calls=can_take_calls,
            coffee_price=coffee_price
        )
        with app.app_context():
            db.session.add(new_cafe)
            db.session.commit()
            print("DEBUG: Cafe added to database successfully!")
            return redirect(url_for('home'))
    except IntegrityError as e:
        db.session.rollback()
        error_message = "A cafe with this name already exists. Please use a unique name."
        print(f"ERROR: IntegrityError during cafe addition: {e}")
        if img_filename and img_filename != "default.png" and os.path.exists(
                os.path.join(app.config['UPLOAD_FOLDER'], img_filename)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
            print(f"DEBUG: Cleaned up uploaded image: {img_filename}")
        return render_template("add_cafe.html", error=error_message), 409
    except Exception as e:
        db.session.rollback()
        print(f"ERROR: Unexpected error during cafe addition: {e}")
        if img_filename and img_filename != "default.png" and os.path.exists(
                os.path.join(app.config['UPLOAD_FOLDER'], img_filename)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
            print(f"DEBUG: Cleaned up uploaded image: {img_filename}")
        return render_template("add_cafe.html",
                               error=f"An error occurred: {e}. Please check your input and try again."), 500


@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def update_cafe_price(cafe_id):
    new_price = request.form.get("coffee_price")
    with app.app_context():
        cafe = db.session.get(Cafe, cafe_id)
        if cafe:
            cafe.coffee_price = new_price
            db.session.commit()
            return jsonify(response={"success": "Successfully updated the price."}), 200
        else:
            return jsonify(error={"Not Found": f"Cafe with id {cafe_id} not found."}), 404


@app.route("/delete-cafe-web/<int:cafe_id>", methods=["POST"])
def delete_cafe_web(cafe_id):
    api_key_provided = request.form.get("api_key")
    if api_key_provided == "TopSecretAPIKey":
        with app.app_context():
            cafe_to_delete = db.session.get(Cafe, cafe_id)
            if cafe_to_delete:
                if not (cafe_to_delete.img_url.startswith('http://') or cafe_to_delete.img_url.startswith('https://')):
                    if cafe_to_delete.img_url and cafe_to_delete.img_url != "default.png":
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], cafe_to_delete.img_url)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"Deleted image file: {file_path}")

                db.session.delete(cafe_to_delete)
                db.session.commit()
                print(f"DEBUG: Cafe with ID {cafe_id} deleted successfully.")
                return redirect(url_for('home'))
            else:
                return "Cafe not found.", 404
    else:
        return "Forbidden: Incorrect API Key.", 403


if __name__ == '__main__':
    app.run(debug=True)
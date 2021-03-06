import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
# Import Werkzeug security helpers
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_recipes")
def get_recipes():
    """
    Home page.
    The function displays all recipes from the database in the carousel.
    """
    recipes = mongo.db.recipes.find()
    return render_template("recipes.html", recipes=recipes)


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    The function allows to register a new user. If a username already
    exists in the database then a message is displayed and the user
    is redirected to the register view. Otherwise, a new user account is
    created and the user is redirected to user's profile page.
    """
    if request.method == "POST":
        # check if username already exists in the db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists! Please try again.")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration complete!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    The function allows an existing user to login. If username and
    password combination matches to the record stored in the database,
    then the user is taken to the user's profile view. Otherwise, a message
    is displayed and the user is redirected to the login view.
    """
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # check if hashed password matches user input
            if check_password_hash(
               existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                return redirect(url_for("profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and Password combination")
                return redirect(url_for("login"))
        else:
            # username doesn't exist
            flash("Incorrect Username and Password combination")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """
    The function allows an existing user to view his/her
    profile page.
    """
    # get session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    if session["user"]:
        return render_template("profile.html", username=username)
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """
    The function removes user from session cookie.
    The user is then redirected to the login view.
    """
    flash("You have been sucessfully logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    """
    The function provides the user with a form to save a new recipe to the
    database. If the function is called using the POST method, then insert the
    data from the form into the database. Otherwise, display the empty form .
    """
    if request.method == "POST":
        recipe = {
            "recipe_name": request.form.get("recipe_name"),
            "category_name": request.form.get("category_name"),
            "difficulty_level": request.form.get("difficulty_level"),
            "recipe_image": request.form.get("recipe_image"),
            "ingredients": request.form.getlist("ingredients"),
            "method": request.form.getlist("method"),
            "added_by": session["user"]
        }
        mongo.db.recipes.insert_one(recipe)
        return redirect(url_for("get_recipes"))

    categories = mongo.db.categories.find()
    difficulty_levels = mongo.db.difficulty_levels.find()
    return render_template(
            "add_recipe.html",
            categories=categories,
            difficulty_levels=difficulty_levels
        )


@app.route("/recipe_details/<recipe_id>")
def recipe_details(recipe_id):
    """
    The function allows users to see the details of a specific recipe
    displayed on the carousel after clicking on the "View Recipe" link.
    """
    return render_template(
        "recipe_details.html", recipe=mongo.db.recipes.find_one(
            {"_id": ObjectId(recipe_id)})
        )


@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    """
    The function allows the user to edit an existing recipe.
    If the function is called using the POST method, then update the
    data from the form in the database.
    """
    if request.method == "POST":
        save_changes = {
            "recipe_name": request.form.get("recipe_name"),
            "category_name": request.form.get("category_name"),
            "difficulty_level": request.form.get("difficulty_level"),
            "recipe_image": request.form.get("recipe_image"),
            "ingredients": request.form.getlist("ingredients"),
            "method": request.form.getlist("method"),
            "added_by": session["user"]
        }
        mongo.db.recipes.replace_one(
            {"_id": ObjectId(recipe_id)}, save_changes
            )

    # retrieve recipe to be edited
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})

    categories = mongo.db.categories.find()
    difficulty_levels = mongo.db.difficulty_levels.find()

    return render_template(
            "edit_recipe.html",
            recipe=recipe,
            categories=categories,
            difficulty_levels=difficulty_levels,
        )


@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    """
    The function allows the user to delete an existing recipe
    from the database when the Delete Recipe button is clicked.
    The user is the redirected to get recipes/home view.
    """
    mongo.db.recipes.delete_one({"_id": ObjectId(recipe_id)})
    flash("The recipe was sucessfully deleted")
    return redirect(url_for("get_recipes"))


@app.route("/get_categories")
def get_categories():
    """
    The function displays all categories from the database
    to admin user.
    """
    categories = list(mongo.db.categories.find())
    return render_template("categories.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    """
    The function provides the user with a form to save a new category to the
    database. If the function is called using the POST method, then insert the
    data from the form into the database.
    Otherwise, display the empty form available to the admin.
    """
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }

        mongo.db.categories.insert_one(category)
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    """
    The function allows the user to edit an existing category.
    If the function is called using the POST method, then update the
    data from the form in the database.
    Otherwise, redirect the admin user to manage categories page.
    """
    # allows user to edit recipe details
    if request.method == "POST":
        save_changes = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.replace_one(
            {"_id": ObjectId(category_id)}, save_changes)
        return redirect(url_for("get_categories"))
    # retrieve category to be edited
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})

    return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    """
    The function allows the admin user to delete an existing category
    from the database when the Delete button is clicked.
    The user is the redirected to manage categories view.
    """
    mongo.db.categories.delete_one({"_id": ObjectId(category_id)})
    return redirect(url_for("get_categories"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)

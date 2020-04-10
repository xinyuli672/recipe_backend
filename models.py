import re
import uuid
import datetime

import flask_sqlalchemy
import sqlalchemy.dialects.postgresql

NAMESPACE_SEARCH = uuid.UUID("0cedf00c175348f4bc102ff7e4ffae5c")

DB = flask_sqlalchemy.SQLAlchemy()

class Recipe(DB.Model):
    meal_id = DB.Column(sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_name = DB.Column(DB.String(255))
    image = DB.Column(sqlalchemy.dialects.postgresql.ARRAY(DB.Text()))
    aggregate_rating = DB.Column(DB.Float)
    author = DB.Column(DB.String(255))
    uploader_id = DB.Column(DB.String(255))
    date_published = DB.Column(DB.Date, default=datetime.date.today)
    src_url = DB.Column(DB.String(255))
    description = DB.Column(DB.Text())
    keywords = DB.Column(sqlalchemy.dialects.postgresql.ARRAY(DB.Text()))
    recipe_category = DB.Column(DB.Text())
    recipe_cuisine = DB.Column(DB.String(255))
    recipe_ingredient = DB.Column(sqlalchemy.dialects.postgresql.ARRAY(DB.Text()))
    # recipe_ingredient_as_string = DB.Column(DB.Text())
    recipe_instructions = DB.Column(sqlalchemy.dialects.postgresql.ARRAY(DB.Text()))
    recipe_yield = DB.Column(DB.String(255))
    # calculated from yield
    recipe_servings = DB.Column(DB.Integer)
    total_time = DB.Column(DB.Interval())

    def __init__(self, from_schema=None, **kwargs):
        """Creates a recipe object either from the keyword arguments or does a conversion from the schema.org schema"""
        if from_schema is None:
            super().__init__(**kwargs)
        else:
            regex_extract_servings = re.compile("(?ai)serves (\d+)")
            recipe_yield = from_schema.get("recipeYield", None)
            if recipe_yield is not None:
                recipe_servings = regex_extract_servings.findall(recipe_yield)
                if not recipe_servings:
                    recipe_servings = None
                else:
                    recipe_servings = int(recipe_servings[0])
            vals = {"meal_name": from_schema.get("name", None),
                    "image": from_schema.get("image", []),
                    "aggregate_rating": from_schema.get("aggregateRating", {}).get("ratingValue", None),
                    "author": from_schema.get("author", {}).get("name", None),
                    "uploader_id": kwargs.get("uploader_id", None),
                    "src_url": kwargs.get("src_url", None),
                    "description": from_schema.get("description", None),
                    "keywords": [s.strip() for s in from_schema.get("keywords", "").split(",")],
                    "recipe_category": from_schema.get("recipeCategory", None),
                    "recipe_cuisine": from_schema.get("recipeCuisine", None),
                    "recipe_ingredient": from_schema.get("recipeIngredient", []),
                    # "recipe_ingredient_as_string": ''.join(from_schema.get("recipeIngredient", [])).lower(),
                    "recipe_instructions": [x.get("text", "") for x in from_schema.get("recipeInstructions", [])],
                    "recipe_yield": recipe_yield,
                    "recipe_servings": recipe_servings,
                    "total_time": from_schema.get("totalTime", None),
                   }
            super().__init__(**vals)

    def get_dict(self):
        """Returns a dictionary representation of this object that can be jsonified."""
        return {"meal_id": self.meal_id.hex,
                "name": self.meal_name,
                "image": self.image,
                "aggregate_rating": self.aggregate_rating,
                "author": self.author,
                "uploader_id": self.uploader_id,
                "src_url": self.src_url,
                "date_published": self.date_published.isoformat(),
                "desciption": self.description,
                "keywords": self.keywords,
                "recipe_category": self.recipe_category,
                "recipe_cuisine": self.recipe_cuisine,
                "recipe_ingredient": self.recipe_ingredient,
                # "recipe_ingredient_as_string": self.recipe_ingredient_as_string,
                "recipe_instructions": self.recipe_instructions,
                "recipe_yield": self.recipe_yield,
                "recipe_servings": self.recipe_servings,
                "total_time": None if self.total_time is None else self.total_time.total_seconds(),
               }

class User(DB.Model):
    user_id = DB.Column(DB.String(255), primary_key=True, nullable=False)
    user_email = DB.Column(DB.String(255), unique=True, nullable=False)
    user_password = DB.Column(DB.String(255), nullable=False)
    user_first_name = DB.Column(DB.String(255), nullable=False)
    user_last_name = DB.Column(DB.String(255), nullable=False)
    security_question = DB.Column(DB.Text(), nullable=False)
    security_answer = DB.Column(DB.Text(), nullable=False)

    def verify_password(self, password):
        if password == self.user_password:
            return True
        else:
            return False


class Search(DB.Model):
    search_id = DB.Column(sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False)
    search_params = DB.Column(DB.PickleType, nullable=False)
    # Update columns as needed to be more efficient. Right now search just stores the pickled dictionary of search options

class Inventory(DB.Model):
    inventory_id = DB.Column(sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = DB.Column(DB.String(255), DB.ForeignKey("user.user_id"))
    user_ingredients = DB.Column(DB.Text())

class SavedRecipe(DB.Model):
    saved_recipe_id = DB.Column(sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = DB.Column(DB.String(255), DB.ForeignKey("user.user_id"))
    meal_id = DB.Column(sqlalchemy.dialects.postgresql.UUID(), DB.ForeignKey("recipe.meal_id"), default=uuid.uuid4)

class Comment(DB.Model):
    comment_id = DB.Column(sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = DB.Column(DB.String(255), DB.ForeignKey("user.user_id"))
    meal_id = DB.Column(sqlalchemy.dialects.postgresql.UUID(as_uuid=True), DB.ForeignKey("recipe.meal_id"))
    user_comment = DB.Column(DB.Text())

    def get_dict(self):
        """Returns a dictionary representation of this object that can be jsonified"""
        return {"comment_id": self.comment_id.hex,
                "user_id": self.user_id,
                "meal_id": self.meal_id.hex,
                "user_comment": self.user_comment
               }

class Report(DB.Model):
    report_id = DB.Column(sqlalchemy.dialects.postgresql.UUID(), primary_key=True, default=uuid.uuid4)
    user_id = DB.Column(DB.String(255), DB.ForeignKey("user.user_id"))
    meal_id = DB.Column(sqlalchemy.dialects.postgresql.UUID(), DB.ForeignKey("recipe.meal_id"), default=uuid.uuid4)
    user_report = DB.Column(DB.Text())

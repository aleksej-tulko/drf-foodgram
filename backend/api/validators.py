import re
from collections import Counter

from django.conf import settings
from rest_framework.validators import ValidationError

from api.constants import NOT_ALLOWED_SYMBOLS
from core.constants import MAX_COOK_TIME, MIN_COOK_TIME

PROHIBITED_RECIPE_NAME = 'Invalid recipe name: {}.'
PROHIBITED_RECIPE_DESCRIPTION = 'Profanity in the description is prohibited.'
PROHIBITED_RECIPE_SYMBOLS = 'The recipe name contains prohibited symbols: {}'
PROHIBITED_RECIPES = ('olivier', 'kholodnik', 'cabbage rolls with filth',)
PROHIBITED_WORDS = ('clown', 'hole', 'ostrich',)
COOKING_TIME_RESTRICTIONS = ('Cooking time must be between '
                             f'{MIN_COOK_TIME} and {MAX_COOK_TIME}')

PROHIBITED_USERNAME = 'Invalid username: {}.'
PROHIBITED_USERNAME_SYMBOLS = ('The username contains '
                               'prohibited symbols: {}')
PROHIBITED_EMAIL_SYMBOLS = r'[^a-z0-9@._]'
PROHIBITED_EMAIL_STRUCTURE = r'^[a-z0-9]+[a-z0-9._]*@[a-z0-9]+\.[a-z]{2,}$'
INVALID_EMAIL_ERROR = 'Email contains prohibited symbols: {}.'
INVALID_EMAIL_STRUCTURE_ERROR = 'Enter a valid email.'
NO_TAGS_PROVIDED = 'The tags field is empty.'
TAGS_NOT_UNIQUE = 'Tags {} are not unique.'
NO_INGREDIENTS_PROVIDED = 'The ingredients field is empty.'
INGREDIENTS_NOT_UNIQUE = 'Ingredients {} are not unique.'


def prohibited_usernames(username):
    if username in settings.PROHIBITED_NAMES:
        raise ValidationError(PROHIBITED_USERNAME.format(username))
    return username


def regex_username(username):
    wrong_symbols = set(re.findall(NOT_ALLOWED_SYMBOLS, username))
    if wrong_symbols:
        raise ValidationError(
            PROHIBITED_USERNAME_SYMBOLS.format(''.join(wrong_symbols))
        )
    return username


def regex_email(email):
    wrong_symbols = set(re.findall(PROHIBITED_EMAIL_SYMBOLS, email))
    if wrong_symbols:
        raise ValidationError(
            INVALID_EMAIL_ERROR.format(''.join(wrong_symbols))
        )
    if not re.fullmatch(PROHIBITED_EMAIL_STRUCTURE, email):
        raise ValidationError(INVALID_EMAIL_STRUCTURE_ERROR)
    return email


def prohibited_recipe_name(name):
    if name.lower() in PROHIBITED_RECIPES:
        raise ValidationError(PROHIBITED_RECIPE_NAME.format(name))
    return name


def regex_recipe_name(name):
    wrong_symbols = set(re.findall(NOT_ALLOWED_SYMBOLS, name))
    if wrong_symbols:
        raise ValidationError(
            PROHIBITED_RECIPE_SYMBOLS.format(''.join(wrong_symbols))
        )
    return name


def prohibited_recipe_description(text):
    if any(word in text for word in PROHIBITED_WORDS):
        raise ValidationError(PROHIBITED_RECIPE_DESCRIPTION)
    return text


def invalid_cooking_time(time):
    if MIN_COOK_TIME > time > MAX_COOK_TIME:
        raise ValidationError(COOKING_TIME_RESTRICTIONS)
    return time


def get_duplicates(data):
    return [item for item, count in Counter(data).items() if count > 1]


def check_ingredients_or_tags(ingredients, tags):
    if not ingredients:
        raise ValidationError(NO_INGREDIENTS_PROVIDED)
    if not tags:
        raise ValidationError(NO_TAGS_PROVIDED)

    all_ingredients = [ingredient['id'] for ingredient in ingredients]

    duplicates = {
        TAGS_NOT_UNIQUE: get_duplicates(tags),
        INGREDIENTS_NOT_UNIQUE: get_duplicates(all_ingredients)
    }

    for validation_msg, duplicate_values in duplicates.items():
        if duplicate_values:
            raise ValidationError(validation_msg.format(duplicate_values))

    return ingredients and tags

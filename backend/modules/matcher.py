from fuzzywuzzy import fuzz
# from db import FARMER_DB
# from modules.db import FARMER_DB
from modules.db import FARMER_DB


def find_best_match(name: str):
    if not name:
        return None, 0

    best_match = None
    best_score = 0

    for db_name in FARMER_DB:
        score = fuzz.ratio(name.lower(), db_name.lower())

        if score > best_score:
            best_score = score
            best_match = db_name

    return best_match, best_score
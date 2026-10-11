"""Public table-sign identities and concise flags from recorded dietary notes."""
import re

# Pattern -> sign flag. Order matters only for how the flags read on the sign.
FLAGS = [
    (r'gluten|coeliac|celiac', 'GF'),
    (r'vegan', 'VEGAN'),
    (r'vegetarian', 'V'),
    (r'pescatarian|pescetarian', 'PESC'),
    (r'halal', 'HALAL'),
    (r'kosher', 'KOSHER'),
    (r'\bnuts?\b|peanut', 'NUT ALLERGY'),
    (r'shellfish', 'NO SHELLFISH'),
    (r'dairy|lactose', 'DAIRY FREE'),
]
NO_REQUIREMENT = ('', 'n/a', 'na', 'nil', 'none', 'normal', 'no dietary requirements', 'no requirements')


def diet_flags(note):
    """Short flags for a dietary note. Anything not recognised stays visible as CHECK NOTE."""
    value = ' '.join((note or '').lower().split())
    if value in NO_REQUIREMENT:
        return []
    flags = []
    for pattern, flag in FLAGS:
        if re.search(pattern, value) and flag not in flags:
            flags.append(flag)
    # A note that says only part of what it means must not be guessed away: a negation or an
    # extra condition ("no", "without", "not", "except") always needs a person to read it.
    if not flags or re.search(r"\b(no|not|without|except)\b", value):
        flags.append('DIET: CHECK NOTE')
    return flags


def table_guests(table, seats, items):
    places = {i['id']: i for i in items if i['template'] == 'place'}
    result = []
    for seat in sorted(seats, key=lambda s: s['seat_number']):
        if seat['table_number'] != table:
            continue
        place = places['place-' + seat['person_id']]
        result.append(dict(guest=place['guest'], character=place['character'],
                           dietaryNote=place['dietaryNote'], flags=diet_flags(place['dietaryNote'])))
    return result

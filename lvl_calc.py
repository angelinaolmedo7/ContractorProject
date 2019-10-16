"""Calculate Rancho Level.

Ranchos have the following levels:

Level 0: 0 xp
Level 1: 200 xp
Level 2: 500 xp
Level 3: 1000 xp
Level 4: 1700 xp
Level 5: 2600 xp
Level 6: 3700 xp
Level 7: 5000 xp
Level 8: 6500 xp
Level 9: 8200 xp
Level 10: 10000 xp

"""


def level_calc(xp):
    """Return the level of a rancho with the passed in xp."""
    if xp >= 10000:
        return 10
    elif xp >= 8200:
        return 9
    elif xp >= 6500:
        return 8
    elif xp >= 5000:
        return 7
    elif xp >= 3700:
        return 6
    elif xp >= 2600:
        return 5
    elif xp >= 1700:
        return 4
    elif xp >= 1000:
        return 3
    elif xp >= 500:
        return 2
    elif xp >= 200:
        return 1
    else:
        return 0

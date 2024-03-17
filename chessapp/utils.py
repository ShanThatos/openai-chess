import string
import random

def rand_id():
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))
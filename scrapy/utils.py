import re

float_number_clear = lambda n: re.sub(r'(\D(?!(\d+)(?!.*(,|\.)\d+)))', '', n).replace(',', '.')

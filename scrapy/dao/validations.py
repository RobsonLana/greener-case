from dict_schema_validator import validator

schemas = {
    'solar_panels': {
        'origin': 'string',
        'updated_at': 'date',
        'port': 'string',
        'price': 'string',
        'structure': ['string', 'null'],
    }
}

def validate (schema, row):
    for err in validator.validate(schema, row):
        print(err['msg'])
        raise err

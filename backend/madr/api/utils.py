from sqlalchemy.exc import IntegrityError


def is_fk_violation(err: IntegrityError) -> bool:
    message = str(err.orig).lower()
    return 'foreign key' in message


def is_unique_violation(err: IntegrityError) -> bool:
    message = str(err.orig).lower()
    return 'unique constraint' in message


def optional_model(cls):
    for field_name, field_info in cls.model_fields.items():
        field_info.annotation |= None
        field_info.default = None
    return cls

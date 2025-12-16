from sqlalchemy.exc import IntegrityError


def is_fk_violation(err: IntegrityError) -> bool:
    message = str(err.orig).lower()
    return 'foreign key' in message


def is_unique_violation(err: IntegrityError) -> bool:
    message = str(err.orig).lower()
    return 'unique constraint' in message

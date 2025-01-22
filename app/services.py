from app.models import User, Advertisement


def create_user(**user_data) -> User:
    return User(**user_data)


def create_adv(**adv_params) -> Advertisement:
    return Advertisement(**adv_params)


def update_user(user: User, new_attrs: dict) -> User:
    for attr, value in new_attrs.items():
        setattr(user, attr, value)
    return user


def get_params(model: User | Advertisement):
    if isinstance(model, User):
        params = {"id": model.id, "name": model.name, "email": model.email,
                  "creation_date": model.creation_date.isoformat()}
        return params
    if isinstance(model, Advertisement):
        params = {"id": model.id, "title": model.title, "description": model.description,
                  "creation_date": model.creation_date.isoformat(), "user_id": model.user_id}
        return params
    return dict()

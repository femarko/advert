from app.domain.models import User, Advertisement


def create_user(**user_data) -> User:
    return User(**user_data)


def create_adv(**adv_params) -> Advertisement:
    return Advertisement(**adv_params)


def update_instance(instance: User | Advertisement, new_attrs: dict) -> User | Advertisement:
    for attr, value in new_attrs.items():
        setattr(instance, attr, value)
    return instance


def get_params(model: User | Advertisement) -> dict[str, str | int]:
    if isinstance(model, User):
        return {
            "id": model.id, "name": model.name, "email": model.email, "creation_date": model.creation_date.isoformat()
        }
    if isinstance(model, Advertisement):
        return {"id": model.id,
                "title": model.title,
                "description": model.description,
                "creation_date": model.creation_date.isoformat(),
                "user_id": model.user_id}
    return dict()

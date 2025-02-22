from datetime import datetime
from typing import Callable, Optional

from app.domain import errors, services, models
from app.repository.filtering import FilterTypes, UserColumns, AdvertisementColumns, Comparison


def create_user(user_data: dict[str, str], validate_func: Callable, hash_pass_func: Callable, uow):
    validated_data = validate_func(**user_data)
    validated_data["password"] = hash_pass_func(password=validated_data["password"])
    user = services.create_user(**validated_data)
    with uow:
        uow.users.add(user)
        uow.commit()
        user_id: int = user.id
        return user_id


def get_user_data(user_id: int, check_current_user_func: Callable, uow):
    current_user_id: int = check_current_user_func(user_id=user_id, get_cuid=True)
    with uow:
        user = uow.users.get(current_user_id)
    user_params: dict[str, str | int] = services.get_params(model=user)
    if user_params:
        return user_params
    raise errors.NotFoundError(message_prefix="The user")




def update_user(user_id: int, check_current_user_func: Callable, validate_func: Callable,
                hash_pass_func: Callable, new_data: dict[str, str], uow) -> dict:
    curent_user_id: int = check_current_user_func(user_id=user_id)
    validated_data: dict[str, str] = validate_func(**new_data)
    if validated_data.get("password"):
        validated_data["password"] = hash_pass_func(password=validated_data["password"])
    with uow:
        current_user: models.User = uow.users.get(instance_id=curent_user_id)
        updated_user = services.update_instance(instance=current_user, new_attrs=validated_data)
        uow.users.add(updated_user)
        uow.commit()
        updated_user_params = services.get_params(model=updated_user)
        return updated_user_params


def delete_user(user_id: int, check_current_user_func: Callable, uow) -> dict[str, str | int]:
    current_user_id: int = check_current_user_func(user_id=user_id)
    with uow:
        user_to_delete: models.User = uow.users.get(current_user_id)
        if not user_to_delete:
            raise errors.NotFoundError
        deleted_user_params: dict[str, str | int] = services.get_params(model=user_to_delete)
        uow.users.delete(user_to_delete)
        uow.commit()
    return deleted_user_params




def get_related_advs(
        authenticated_user_id: int, check_current_user_func: Callable, uow, page: Optional[int] = None,
        per_page: Optional[int] = None
) -> dict[str, int | list[dict[str, str | int]]]:

    current_user_id = check_current_user_func(user_id=authenticated_user_id)
    with uow:
        paginated_data = uow.advs.get_list_or_paginated_data(
            filter_type=FilterTypes.COLUMN_VALUE, comparison=Comparison.IS, column=AdvertisementColumns.USER_ID,
            column_value=current_user_id, paginate=True, page=page, per_page=per_page
        )
    if paginated_data["items"]:
        return paginated_data
    raise errors.NotFoundError(base_message="The related advertisements are not found.")


def create_adv(get_auth_user_id_func: Callable, validate_func: Callable, adv_params: dict[str, str | int], uow) -> int:
    authenticated_user_id: int = get_auth_user_id_func()
    validated_data = validate_func(**adv_params)
    validated_data |= {"user_id": authenticated_user_id}
    adv = services.create_adv(**validated_data)
    with uow:
        uow.advs.add(adv)
        uow.commit()
        return adv.id


def search_advs_by_text(
        uow,
        column_value: str | int | datetime,
        column: Optional[str] = None,
        page: Optional[str] = None,
        per_page: Optional[str] = None
) -> dict[str, str | int]:
    if not column:
        column = "description"
    with uow:
        paginated_res: dict[str, int | list[dict[str, str | int]]] = uow.advs.get_list_or_paginated_data(
            filter_type=FilterTypes.SEARCH_TEXT, comparison=Comparison.IS, column=column, column_value=column_value,
            page=page, per_page=per_page, paginate=True
        )
    paginated_res["items"] = [
        {params_dict["title"]: params_dict["description"]} for params_dict in paginated_res["items"]
    ]
    return paginated_res


def get_adv_params(adv_id: int, check_current_user_func: Callable, uow) -> dict[str, str | int]:
    with uow:
        adv: models.Advertisement = uow.advs.get(instance_id=adv_id)
    try:
        check_current_user_func(user_id=adv.user_id)
        return services.get_params(model=adv)
    except AttributeError:
        raise errors.NotFoundError(message_prefix="The advertisement")


def update_adv(
        adv_id: int, new_params: dict, check_current_user_func: Callable, validate_func: Callable, uow
) -> dict[str, str | int]:
    with uow:
        adv: models.Advertisement = uow.advs.get(instance_id=adv_id)
        if not adv:
            raise errors.NotFoundError(message_prefix="The advertisement")
        check_current_user_func(user_id=adv.user_id)
        validated_data: dict[str, str] = validate_func(**new_params)
        updated_adv: models.Advertisement = services.update_instance(instance=adv, new_attrs=validated_data)
        uow.advs.add(updated_adv)
        uow.commit()
        updated_adv_params: dict = services.get_params(model=updated_adv)
        return updated_adv_params


def delete_adv(adv_id: int, get_auth_user_id_func: Callable, uow) -> dict[str, str | int]:
    authenticated_user_id: int = get_auth_user_id_func()
    with uow:
        adv_to_delete = uow.advs.get(adv_id)
        try:
            if adv_to_delete.user_id == authenticated_user_id:
                deleted_adv_params: dict[str, str | int] = services.get_params(model=adv_to_delete)
                uow.advs.delete(adv_to_delete)
                uow.commit()
                return deleted_adv_params
            raise errors.CurrentUserError
        except AttributeError:
            raise errors.NotFoundError(message_prefix="The advertisement")


def jwt_auth(validate_func: Callable, check_pass_func: Callable[..., bool], grant_access_func: Callable,
             credentials: dict, uow) -> str:
    validated_data = validate_func(**credentials)
    with uow:
        list_of_users: list[models.User] = uow.users.get_list_or_paginated_data(
            filter_type=FilterTypes.COLUMN_VALUE, comparison=Comparison.IS, column=UserColumns.EMAIL,
            column_value=validated_data[UserColumns.EMAIL]
        )
    try:
        user: models.User = list_of_users[0]
    except IndexError:
        raise errors.AccessDeniedError
    if check_pass_func(password=validated_data["password"], hashed_password=user.password):
        access_token: str = grant_access_func(identity=user.id)
        return access_token
    raise errors.AccessDeniedError

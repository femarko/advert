from app import errors


def fake_check_current_user_func(user_id: int, get_cuid: bool = True):
    return user_id


def fake_validate_func(**data):
    return data


def fake_hash_pass_func(password: str):
    return password


class FakeUsersRepo:
    def __init__(self, users: list):
        self.users = set()
        self.temp_users = []
        self.add_called = False

    def add(self, user):
        self.add_called = True
        self.temp_users.append(user)

    def get(self, user_id):
        return next(user for user in self.users if user.id == user_id)


class FakeAdvsRepo:
    def __init__(self, advs: list):
        self.advs = set()

    def add(self, adv):
        self.advs.add(adv)

    def get(self, adv_id):
        return next(adv for adv in self.advs if adv_id.id == adv_id)


class FakeUnitOfWork():
    def __init__(self):
        self.commited = False

    def __enter__(self):
        self.users = FakeUsersRepo([])
        self.advs = FakeAdvsRepo([])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()

    def rollback(self):
        pass

    def commit(self):
        if self.users.add_called:
            if len(self.users.temp_users + list(self.users)) != len(set(self.users.temp_users + list(self.users))):
                raise errors.AlreadyExistsError
            self.commited = True

from pydantic import BaseModel


class M3(BaseModel):
    x: int = 1
    y: str = 'hello'


class UserM(M3):
    x: int = 10


class M3Getter:

    def __init__(self):
        self._has_read_user_conf = False


    def get(self):
        m = M3()
        if not self._has_read_user_conf:
            for k, v in UserM().dict().items():
                setattr(m, k, v)
        else:
            self._has_read_user_conf = True

        return m


M3Getter().get().x

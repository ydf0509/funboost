
from pydantic import BaseModel,deprecated,Field

class M1(BaseModel):

    a :int= Field()
from pydantic import BaseModel


class App(BaseModel):
    id: str = None

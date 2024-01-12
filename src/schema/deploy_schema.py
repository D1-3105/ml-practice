from pydantic import BaseModel


class DeployResponseSchema(BaseModel):
    server_state: int
    id: int
    model_id: int


class DeployResultSchema(BaseModel):
    current_port: int | None
    current_host: str | None
    server_state: int

from pydantic import (
    BaseModel,
    Field
)


class SpeakRequest(BaseModel):

    text: str = Field(
        ...,
        min_length=1,
        description="Text to convert into speech"
    )
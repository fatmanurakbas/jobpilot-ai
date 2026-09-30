from pydantic import BaseModel


class BrowserReviewResultRequest(BaseModel):
    screenshot_base64: str
    final_url: str
    verification: dict

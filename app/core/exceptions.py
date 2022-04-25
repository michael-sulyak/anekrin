class ValidationError(Exception):
    msg: str
    is_markdown: bool

    def __init__(self, msg: str, *, is_markdown: bool = False) -> None:
        self.msg = msg
        self.is_markdown = is_markdown

    def __repr__(self) -> str:
        return self.msg

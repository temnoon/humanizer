from typing import Callable, Any
from click import Command, Group

ClickHandler = Callable[..., Any]
ClickCommand = Command
ClickGroup = Group

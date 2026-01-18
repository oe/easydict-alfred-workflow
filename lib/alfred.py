"""
Easydict Alfred Workflow - Alfred Output Formatting

Generates Alfred Script Filter JSON output.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Any


@dataclass
class AlfredMod:
    """Alfred modifier key configuration."""
    valid: bool = True
    arg: str = ""
    subtitle: str = ""


@dataclass 
class AlfredItem:
    """Alfred Script Filter item."""
    title: str
    subtitle: str = ""
    arg: str = ""
    valid: bool = True
    icon: Optional[dict] = None
    mods: Optional[dict] = None
    text: Optional[dict] = None
    quicklookurl: Optional[str] = None
    uid: Optional[str] = None
    autocomplete: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary, removing None values."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                result[key] = value
        return result
    
    @classmethod
    def create(
        cls,
        title: str,
        subtitle: str = "",
        arg: str = "",
        icon_path: Optional[str] = None,
        copy_text: Optional[str] = None,
        largetype: Optional[str] = None,
        alt_subtitle: Optional[str] = None,
        alt_arg: Optional[str] = None,
        cmd_subtitle: Optional[str] = None,
        cmd_arg: Optional[str] = None,
    ) -> "AlfredItem":
        """Create an Alfred item with common options."""
        item = cls(
            title=title,
            subtitle=subtitle,
            arg=arg or title,
        )
        
        if icon_path:
            item.icon = {"path": icon_path}
        
        # Text for copy and large type
        if copy_text or largetype:
            item.text = {}
            if copy_text:
                item.text["copy"] = copy_text
            if largetype:
                item.text["largetype"] = largetype
        
        # Modifier keys
        mods = {}
        if alt_subtitle or alt_arg:
            mods["alt"] = {
                "valid": True,
                "arg": alt_arg or arg,
                "subtitle": alt_subtitle or "",
            }
        if cmd_subtitle or cmd_arg:
            mods["cmd"] = {
                "valid": True, 
                "arg": cmd_arg or arg,
                "subtitle": cmd_subtitle or "",
            }
        if mods:
            item.mods = mods
            
        return item


@dataclass
class AlfredOutput:
    """Alfred Script Filter output."""
    items: list = field(default_factory=list)
    rerun: Optional[float] = None
    
    def add_item(self, item: AlfredItem):
        """Add an item to the output."""
        self.items.append(item)
    
    def add_error(self, title: str, subtitle: str = ""):
        """Add an error item."""
        self.add_item(AlfredItem(
            title=title,
            subtitle=subtitle,
            valid=False,
            icon={"path": "icons/error.png"},
        ))
    
    def add_loading(self, title: str = "Loading...", subtitle: str = ""):
        """Add a loading item."""
        self.add_item(AlfredItem(
            title=title,
            subtitle=subtitle,
            valid=False,
        ))
    
    def to_json(self) -> str:
        """Convert to Alfred JSON format."""
        output = {
            "items": [item.to_dict() for item in self.items]
        }
        if self.rerun:
            output["rerun"] = self.rerun
        return json.dumps(output, ensure_ascii=False, indent=2)
    
    def print(self):
        """Print JSON output for Alfred."""
        print(self.to_json())

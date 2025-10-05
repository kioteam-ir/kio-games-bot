from dataclasses import dataclass
from typing import Dict

@dataclass
class CallbackData:
    command: str
    args   : Dict[str, str]

    @classmethod
    def parse(cls, data: str) -> 'CallbackData':
        # Split by ":" → command and parameters
        cmd, *rest = data.split(":", 1)
        params_str = rest[0] if rest else ""
        args = {}
        if params_str:
            for item in params_str.split(","):
                if "=" in item:
                    k, v = item.split("=", 1)
                    args[k] = v
                else:
                    args[item] = None
        return cls(cmd, args)

    def build(self) -> str:
        params = ",".join(
            f"{k}={v}" if v is not None else k
            for k, v in self.args.items()
        )
        return f"{self.command}:{params}" if params else self.command

if __name__ == "__main__":
    # Example usage
    
    data = CallbackData(
        command="change_lang",
        args={"to": "en"}
    )
    
    callback_str = data.build()
    print(callback_str)  # Output: "change_lang:to=en"
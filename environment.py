from llvmlite import ir
from typing import Optional

class Environment:
    def __init__(
        self,
        records: Optional[dict[str, tuple[ir.Value, ir.Type]]] = None,
        parent: Optional["Environment"] = None,
        name: str = "global",
    ) -> None:
        self.records: dict[str, tuple[ir.Value, ir.Type]] = records if records else {}
        self.parent: Optional[Environment] = parent
        self.name: str = name


    def define(self, name: str, ptr: ir.Value, _type: ir.Type) -> ir.Value:
        self.records[name] = (ptr, _type)
        return ptr
    
    def lookup(self, name: str) -> Optional[tuple[ir.Value, ir.Type]]:
        return self.__resolve(name)

    def __resolve(self, name: str) -> Optional[tuple[ir.Value, ir.Type]]:
        if name in self.records:
            return self.records[name]
        elif self.parent:
            return self.parent.__resolve(name)
        else:
            return None
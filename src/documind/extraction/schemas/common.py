from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

try:
    from pydantic import BaseModel, ConfigDict

    class BaseExtractionModel(BaseModel):
        model_config = ConfigDict(extra="forbid", populate_by_name=True)

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()
except ImportError:
    class BaseExtractionModel:  # type: ignore[no-redef]
        def __init__(self, **kwargs: Any) -> None:
            # Populate class-level attributes first
            for attr in dir(self.__class__):
                if not attr.startswith("__") and not callable(getattr(self.__class__, attr)) and attr != "model_config":
                    setattr(self, attr, getattr(self.__class__, attr))
            for k, v in kwargs.items():
                setattr(self, k, v)

        def to_dict(self) -> Dict[str, Any]:
            res = {}
            for k, v in self.__dict__.items():
                if isinstance(v, BaseExtractionModel):
                    res[k] = v.to_dict()
                elif isinstance(v, list):
                    res[k] = [item.to_dict() if isinstance(item, BaseExtractionModel) else item for item in v]
                else:
                    res[k] = v
            return res

        @classmethod
        def model_validate(cls, data: Dict[str, Any]) -> "BaseExtractionModel":
            return cls(**data)


class Party(BaseExtractionModel):
    name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    address: Optional[str] = None
    state_code: Optional[str] = None  # 2-digit GST state code e.g. "27"


class InvoiceLine(BaseExtractionModel):
    description: Optional[str] = None
    hsn_sac: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    taxable_value: Optional[Decimal] = None
    gst_rate: Optional[Decimal] = None  # Total GST percentage e.g. 18.0
    line_total: Optional[Decimal] = None

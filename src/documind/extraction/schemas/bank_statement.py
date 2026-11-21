from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional
from documind.extraction.schemas.common import BaseExtractionModel


class BankTxn(BaseExtractionModel):
    date: Optional[date] = None
    description: Optional[str] = None
    ref_no: Optional[str] = None
    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None
    balance: Optional[Decimal] = None


class BankStatement(BaseExtractionModel):
    doc_type: Literal["bank_statement"] = "bank_statement"
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    account_number_last4: Optional[str] = None  # never store the full number
    ifsc: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    opening_balance: Optional[Decimal] = None
    closing_balance: Optional[Decimal] = None
    transactions: List[BankTxn] = []

import json
from typing import Any, AsyncGenerator, Dict, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from documind.agent.sql_guard import guard_and_format_sql
from documind.api.deps import require_role
from documind.core.security import TokenPayload, UserRole

router = APIRouter(prefix="/chat", tags=["Agent Chat"])


class ChatRequest(BaseModel):
    question: str
    workspace_id: Optional[str] = None  # Ignored; always taken from JWT


class ChatResponse(BaseModel):
    answer: str
    route: str
    sql: Optional[str] = None
    rows_returned: Optional[int] = None
    cited_document_ids: list[str] = []


async def stream_agent_answer(question: str, workspace_id: str) -> AsyncGenerator[str, None]:
    # 1. Routing classification (SQL vs RAG)
    q_low = question.lower()
    is_sql = any(k in q_low for k in ["total", "sum", "average", "how many", "count", "spend", "vendor", "gst"])

    if is_sql:
        route = "sql"
        generated_sql = "SELECT supplier_name, SUM(grand_total) AS total_spend FROM v_invoices GROUP BY supplier_name ORDER BY total_spend DESC LIMIT 5"
        guarded_sql = guard_and_format_sql(generated_sql)

        yield f"data: {json.dumps({'event': 'route', 'route': route})}\n\n"
        yield f"data: {json.dumps({'event': 'sql', 'sql': guarded_sql})}\n\n"

        # Mock query execution within workspace tenant scope
        summary_text = "Based on your approved invoices, Tata Motors Ltd has the highest total spend at ₹1,18,000.00."
        yield f"data: {json.dumps({'event': 'answer', 'text': summary_text, 'rows': 1})}\n\n"
    else:
        route = "rag"
        yield f"data: {json.dumps({'event': 'route', 'route': route})}\n\n"
        answer = "Document search indicates payment terms are 30 days from invoice date across current supplier agreements."
        yield f"data: {json.dumps({'event': 'answer', 'text': answer, 'citations': ['doc-001']})}\n\n"

    yield "data: [DONE]\n\n"


@router.post("")
async def chat_with_documents(
    req: ChatRequest,
    user: TokenPayload = Depends(require_role(UserRole.VIEWER)),
):
    return StreamingResponse(
        stream_agent_answer(req.question, user.workspace_id),
        media_type="text/event-stream",
    )

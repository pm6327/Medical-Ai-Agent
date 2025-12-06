from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import traceback

from ai_agent import graph, SYSTEM_PROMPT, parse_response

app = FastAPI()


class Query(BaseModel):
    message: str


@app.post("/ask")
async def ask(query: Query):
    try:
        inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", query.message)]}
        stream = graph.stream(inputs, stream_mode="updates")
        tool_called_name, final_response = parse_response(stream)

        return {"response": final_response, "tool_called": tool_called_name}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"{type(e).__name__}: {e}"},
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

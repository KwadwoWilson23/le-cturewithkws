import json
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from services.live_session_service import (
    create_lecture_plan,
    create_session,
    get_session,
    remove_session,
)

router = APIRouter()


class LecturePlanRequest(BaseModel):
    notes_context: str


@router.post("/live-session/plan")
async def get_lecture_plan(request: LecturePlanRequest):
    try:
        segments = await create_lecture_plan(request.notes_context)
        return {"segments": segments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create lecture plan: {str(e)}")


class StartSessionRequest(BaseModel):
    notes_context: str
    segments: list


@router.post("/live-session/start")
async def start_session(request: StartSessionRequest):
    session_id = create_session(request.notes_context, request.segments)
    return {"session_id": session_id}


@router.websocket("/ws/live-session/{session_id}")
async def live_session_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()

    manager = get_session(session_id)
    if not manager:
        await websocket.send_json({"type": "error", "message": "Session not found"})
        await websocket.close()
        return

    async def audio_callback(audio_data: bytes):
        try:
            await websocket.send_bytes(audio_data)
        except Exception:
            pass

    async def text_callback(text: str):
        try:
            await websocket.send_json({"type": "ai_text", "text": text})
        except Exception:
            pass

    async def segment_done_callback(segment_index: int):
        try:
            await websocket.send_json({
                "type": "segment_complete",
                "segment_index": segment_index,
            })
        except Exception:
            pass

    try:
        await manager.connect(audio_callback, text_callback, segment_done_callback)

        await websocket.send_json({
            "type": "connected",
            "total_segments": len(manager.segments),
        })

        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                await manager.send_voice_input(message["bytes"])

            elif "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")

                if msg_type == "next_segment":
                    segment_index = data.get("segment_index", manager.current_segment + 1)
                    if segment_index < len(manager.segments):
                        await websocket.send_json({
                            "type": "segment_start",
                            "segment_index": segment_index,
                            "segment": manager.segments[segment_index],
                        })
                        await manager.start_segment(segment_index)
                    else:
                        await websocket.send_json({
                            "type": "lecture_complete",
                            "message": "All segments covered! Great session!",
                        })

                elif msg_type == "start_first_segment":
                    await websocket.send_json({
                        "type": "segment_start",
                        "segment_index": 0,
                        "segment": manager.segments[0],
                    })
                    await manager.start_segment(0)

                elif msg_type == "text_question":
                    question = data.get("text", "")
                    if question:
                        await manager.send_text_question(question)
                except json.JSONDecodeError as e:
                    await websocket.send_json({"type": "error", "message": f"Invalid JSON: {str(e)}"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        await manager.close()
        remove_session(session_id)

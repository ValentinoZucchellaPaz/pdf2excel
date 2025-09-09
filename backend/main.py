from fastapi import FastAPI, File, Request, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Límite de tamaño (ej: 5 MB = 5 * 1024 * 1024)
MAX_FILE_SIZE = 5 * 1024 * 1024  

from converter import convert_pdf_2_excel, check_plantilla1

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def ping():
    return {"message": "pong"}

@app.post("/convert")
async def convert(request: Request, file: UploadFile = File(...), plantilla: int = Form(...)):
    # 1) Verificar tamaño máximo
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="El archivo excede el tamaño máximo (5 MB)")

    # 2) Seleccionar plantilla
    if plantilla == 1:
        if not check_plantilla1(file):
            raise HTTPException(status_code=400, detail="El PDF no corresponde a la plantilla 1")
        excel_buffer = convert_pdf_2_excel(file)
    else:
        raise HTTPException(status_code=400, detail=f"Plantilla {plantilla} no soportada")

    # 3) Devolver Excel en memoria
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={file.filename}.xlsx"},
    )
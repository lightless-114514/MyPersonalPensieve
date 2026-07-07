import os
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:17890"
os.environ["HTTP_PROXY"] = "http://127.0.0.1:17890"
import uvicorn
uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

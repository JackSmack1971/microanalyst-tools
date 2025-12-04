import uvicorn
import os

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    print(f"Starting Microanalyst API on {host}:{port}...")
    uvicorn.run("src.api.server:app", host=host, port=port, reload=True)

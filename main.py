import os
from html import escape
from urllib.parse import quote

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse


app = FastAPI(title="Azure File Downloader")


# --------------------------------------------------
# Azure configuration
# --------------------------------------------------

AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
AZURE_TARGET_FOLDER = os.getenv(
    "AZURE_TARGET_FOLDER",
    ""
).strip("/")


if not AZURE_CONNECTION_STRING:
    raise RuntimeError(
        "AZURE_CONNECTION_STRING environment variable is missing."
    )

if not AZURE_CONTAINER_NAME:
    raise RuntimeError(
        "AZURE_CONTAINER_NAME environment variable is missing."
    )


blob_service_client = BlobServiceClient.from_connection_string(
    AZURE_CONNECTION_STRING
)

container_client = blob_service_client.get_container_client(
    AZURE_CONTAINER_NAME
)


# --------------------------------------------------
# Frontend webpage
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    try:
        prefix = (
            f"{AZURE_TARGET_FOLDER}/"
            if AZURE_TARGET_FOLDER
            else None
        )

        blobs = container_client.list_blobs(
            name_starts_with=prefix
        )

        file_cards = ""

        for blob in blobs:
            blob_name = blob.name

            if prefix and blob_name.startswith(prefix):
                file_name = blob_name[len(prefix):]
            else:
                file_name = blob_name

            if not file_name:
                continue

            safe_name = escape(file_name)
            encoded_name = quote(file_name, safe="")

            file_size_mb = round(
                blob.size / (1024 * 1024),
                2
            )

            file_cards += f"""
            <div class="file-card">
                <div class="file-info">
                    <div class="file-icon">📄</div>

                    <div>
                        <h3>{safe_name}</h3>
                        <p>Size: {file_size_mb} MB</p>
                        <p>
                            Last modified:
                            {blob.last_modified.strftime("%d %B %Y, %I:%M %p")}
                        </p>
                    </div>
                </div>

                <a
                    class="download-button"
                    href="/download/{encoded_name}"
                >
                    Download
                </a>
            </div>
            """

        if not file_cards:
            file_cards = """
            <div class="empty-state">
                <div class="empty-icon">📁</div>
                <h2>No files available</h2>
                <p>No downloadable files were found in the configured folder.</p>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1.0"
            >

            <title>File Download Portal</title>

            <style>
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}

                body {{
                    font-family:
                        Arial,
                        Helvetica,
                        sans-serif;

                    background:
                        linear-gradient(
                            135deg,
                            #eef2ff,
                            #f8fafc
                        );

                    min-height: 100vh;
                    color: #1e293b;
                }}

                .header {{
                    background:
                        linear-gradient(
                            135deg,
                            #2563eb,
                            #1e40af
                        );

                    color: white;
                    padding: 32px 20px;
                    text-align: center;
                    box-shadow:
                        0 4px 18px
                        rgba(15, 23, 42, 0.18);
                }}

                .header h1 {{
                    font-size: 32px;
                    margin-bottom: 10px;
                }}

                .header p {{
                    font-size: 16px;
                    opacity: 0.9;
                }}

                .container {{
                    width: min(1000px, 92%);
                    margin: 40px auto;
                }}

                .section-title {{
                    margin-bottom: 20px;
                }}

                .section-title h2 {{
                    font-size: 24px;
                    margin-bottom: 6px;
                }}

                .section-title p {{
                    color: #64748b;
                }}

                .file-card {{
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 20px;

                    background: white;
                    padding: 22px;
                    margin-bottom: 16px;
                    border-radius: 14px;

                    box-shadow:
                        0 8px 24px
                        rgba(15, 23, 42, 0.08);

                    border:
                        1px solid #e2e8f0;

                    transition:
                        transform 0.2s ease,
                        box-shadow 0.2s ease;
                }}

                .file-card:hover {{
                    transform: translateY(-2px);

                    box-shadow:
                        0 12px 30px
                        rgba(15, 23, 42, 0.12);
                }}

                .file-info {{
                    display: flex;
                    align-items: center;
                    gap: 18px;
                    min-width: 0;
                }}

                .file-icon {{
                    width: 58px;
                    height: 58px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 12px;
                    background: #dbeafe;
                    font-size: 30px;
                    flex-shrink: 0;
                }}

                .file-info h3 {{
                    font-size: 18px;
                    margin-bottom: 8px;
                    overflow-wrap: anywhere;
                }}

                .file-info p {{
                    color: #64748b;
                    font-size: 14px;
                    margin-top: 4px;
                }}

                .download-button {{
                    display: inline-block;
                    text-decoration: none;
                    background: #2563eb;
                    color: white;
                    padding: 12px 22px;
                    border-radius: 9px;
                    font-weight: bold;
                    white-space: nowrap;
                    transition: background 0.2s ease;
                }}

                .download-button:hover {{
                    background: #1d4ed8;
                }}

                .empty-state {{
                    background: white;
                    padding: 60px 20px;
                    text-align: center;
                    border-radius: 14px;
                    box-shadow:
                        0 8px 24px
                        rgba(15, 23, 42, 0.08);
                }}

                .empty-icon {{
                    font-size: 52px;
                    margin-bottom: 18px;
                }}

                .empty-state h2 {{
                    margin-bottom: 10px;
                }}

                .empty-state p {{
                    color: #64748b;
                }}

                .footer {{
                    text-align: center;
                    color: #64748b;
                    padding: 30px 20px;
                    font-size: 14px;
                }}

                @media (max-width: 650px) {{
                    .header h1 {{
                        font-size: 26px;
                    }}

                    .file-card {{
                        flex-direction: column;
                        align-items: stretch;
                    }}

                    .download-button {{
                        text-align: center;
                        width: 100%;
                    }}
                }}
            </style>
        </head>

        <body>
            <header class="header">
                <h1>File Download Portal</h1>

                <p>
                    Select a file below to download it securely.
                </p>
            </header>

            <main class="container">
                <div class="section-title">
                    <h2>Available Files</h2>

                    <p>
                        Files are fetched directly from Azure Blob Storage.
                    </p>
                </div>

                {file_cards}
            </main>

            <footer class="footer">
                Powered by FastAPI and Azure Blob Storage
            </footer>
        </body>
        </html>
        """

    except AzureError as exc:
        return HTMLResponse(
            content=f"""
            <html>
                <body style="
                    font-family: Arial;
                    padding: 40px;
                    background: #f8fafc;
                ">
                    <h1>Unable to load files</h1>

                    <p>
                        {escape(str(exc))}
                    </p>
                </body>
            </html>
            """,
            status_code=500
        )


# --------------------------------------------------
# JSON endpoint to list files
# --------------------------------------------------

@app.get("/api/files")
def list_files_api():
    try:
        prefix = (
            f"{AZURE_TARGET_FOLDER}/"
            if AZURE_TARGET_FOLDER
            else None
        )

        blobs = container_client.list_blobs(
            name_starts_with=prefix
        )

        files = []

        for blob in blobs:
            blob_name = blob.name

            if prefix and blob_name.startswith(prefix):
                file_name = blob_name[len(prefix):]
            else:
                file_name = blob_name

            if file_name:
                files.append({
                    "file_name": file_name,
                    "size_bytes": blob.size,
                    "last_modified": blob.last_modified,
                    "download_url": f"/download/{quote(file_name, safe='')}"
                })

        return {
            "total_files": len(files),
            "files": files
        }

    except AzureError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


# --------------------------------------------------
# Download file endpoint
# --------------------------------------------------

@app.get("/download/{file_name:path}")
def download_file(file_name: str):
    try:
        clean_file_name = file_name.strip("/")

        if not clean_file_name:
            raise HTTPException(
                status_code=400,
                detail="File name is required."
            )

        if AZURE_TARGET_FOLDER:
            blob_name = (
                f"{AZURE_TARGET_FOLDER}/"
                f"{clean_file_name}"
            )
        else:
            blob_name = clean_file_name

        blob_client = container_client.get_blob_client(
            blob=blob_name
        )

        properties = blob_client.get_blob_properties()
        stream = blob_client.download_blob()

        download_name = clean_file_name.split("/")[-1]

        content_type = (
            properties.content_settings.content_type
            or "application/octet-stream"
        )

        encoded_download_name = quote(
            download_name,
            safe=""
        )

        return StreamingResponse(
            stream.chunks(),
            media_type=content_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{download_name}"; '
                    f"filename*=UTF-8''{encoded_download_name}"
                )
            }
        )

    except HTTPException:
        raise

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="File not found."
        ) from exc

    except AzureError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to download file: {str(exc)}"
        ) from exc


# --------------------------------------------------
# Health endpoint
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
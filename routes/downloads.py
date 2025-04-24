
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import mimetypes,os
from config import Config
from utils.yt_handler_YTDLP import download_stream,download_and_merge,get_playlist_songs,get_youtube_video_details
from utils.globalDb import insert_download
from typing import Optional
from config import Config
import asyncio

router = APIRouter()
mydb = Config.mydb
mycursor = mydb.cursor()

class DownloadRequest(BaseModel):
    song_url: str
    songId: str
    itag: str
    filename: str
    start_byte: Optional[int] = 0
    userId: str = None
    size_mb: Optional[float] = None
    thumbnailUrl: Optional[str] = None
    ext: str = 'mp4'

@router.post("/download/yt")
async def download_video(request: Request, data: DownloadRequest):
    print("Processing download request...")
    
    try:
        url = data.song_url
        song_id = data.songId
        itag = data.itag
        filename = data.filename
        start_byte = data.start_byte
        user_id = data.userId
        file_size = data.size_mb
        thumbnail = data.thumbnailUrl
        ext = data.ext

        if not url or not itag or not filename:
            raise HTTPException(status_code=400, detail="songId, itag, and filename are required")

        dwnload_id = url

        if user_id:
            responce = await insert_download(
                user_id=user_id,
                song_id=song_id,
                file_name=filename,
                file_format=ext,
                itag=itag,
                file_size=file_size,
                file_source="youtube",
                thumbnail=thumbnail,
                user_agent=request.headers.get('User-Agent'),
                is_partial=(start_byte > 0),
                downloaded_size=0
            )

            if responce.get('download_id') and responce.get('download_id') is not None:
                dwnload_id = str(responce.get('download_id'))
               

        content_type, _ = mimetypes.guess_type(filename + ext)
        if not content_type:
            content_type = "video/mp4"

        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Accept-Ranges': 'bytes',
            'X-Download-URL': dwnload_id,
            'format': ext,
        }

        stream = (
            download_stream(url, itag, start_byte) 
            if itag in {'18', '140', '152'} 
            else download_and_merge(url, itag, '140')
        )

        return StreamingResponse(
            stream,
            media_type=content_type,
            headers=headers
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




@router.post('/download/injustify')
async def download_video_local(request: Request, data: DownloadRequest):
    if not data.filename or not data.songId or not data.itag:
        raise HTTPException(status_code=400, detail="songId, itag, and filename are required")

    file_path = os.path.join(Config.SONGS_FOLDER, data.song_url)

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found")

    responce = {}
    if data.userId and data.songId: 
        responce = await insert_download(
            user_id=data.userId,
            song_id=data.songId,
            file_name=data.filename,
            file_format=data.itag,
            itag=data.itag,
            file_size=data.size_mb,
            file_source="injustify",
            thumbnail=data.thumbnailUrl,
            user_agent=request.headers.get('User-Agent'),
            is_partial=(data.start_byte > 0),
        )

    dwnload_id = responce.get('download_id', data.songId)  # Default to song_id if download_id is missing
    file_size = os.path.getsize(file_path)

    if data.start_byte >= file_size:
        raise HTTPException(status_code=416, detail="Requested range not satisfiable")

    end_byte = file_size - 1  # Last byte index
    content_range = f"bytes {data.start_byte}-{end_byte}/{file_size}"

    mime_type, _ = mimetypes.guess_type(file_path)
    content_type = mime_type or 'video/mp4'

    ascii_filename = data.filename.encode('ascii', 'ignore').decode()
    disposition_filename = f"filename*=UTF-8''{ascii_filename}"

    headers = {
        'Content-Type': content_type,
        'Content-Disposition': f'attachment; {disposition_filename}',
        'Content-Range': content_range,
        'Content-Length': str(end_byte - data.start_byte + 1),
        'X-Download-URL': str(dwnload_id),
        'format': data.ext,
    }

    return StreamingResponse(
        download_stream_local(file_path, data.start_byte),
        status_code=206,
        headers=headers
    )

def download_stream_local(file_path, start_byte=0):
    try:
        chunk_size = 1024 * 1024  # 1MB chunks
        with open(file_path, 'rb') as f:
            f.seek(start_byte)
            while chunk := f.read(chunk_size):
                yield chunk
    except Exception as e:
        print(f"Error streaming file: {e}")


class playlistdetils (BaseModel):
    userId: str = None
    playlistUrl: str = None

@router.post('/playlist/youtube')
async def get_youtube_songs(request: Request, data: playlistdetils):
    """Improved endpoint with better validation"""
    if not data.playlistUrl:
        raise HTTPException(status_code=400, detail="Playlist URL is required")

    try:
        # # Validate URL format
        # if "youtube.com/playlist?" not in data.playlistUrl and "youtube.com/watch?list=" not in data.playlistUrl:
        #     raise HTTPException(status_code=400, detail="Invalid YouTube playlist URL format")

        songs = await get_playlist_songs(data.playlistUrl)
        
        if not songs:
            raise HTTPException(
                status_code=404,
                detail="No songs found in playlist (might be private, empty, or unviewable)"
            )

        return {
            "status": "success",
            "count": len(songs),
            "songs": songs
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process playlist: {str(e)}"
        )
    

class YTDetailsRequest(BaseModel):
    video_urls: list[str]
    userId:Optional[str] = None

from typing import List, Optional, Dict, Union

@router.post("/yt/details")
async def get_youtube_song_details(request: Request, data: YTDetailsRequest):
    if not data.video_urls:
        raise HTTPException(status_code=400, detail="video_urls is required")

    try:
        # Await the batch fetch
        songdetails: Dict[str, Union[Dict, str]] = await get_youtube_video_details(data.video_urls)

        return {
            "status": "success",
            "count": len(songdetails),
            "song_details": songdetails
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
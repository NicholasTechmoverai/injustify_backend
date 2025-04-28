import yt_dlp
import re
import requests
import asyncio
import threading
from queue import Queue
import urllib.parse
import aiohttp
import asyncio
import tempfile
import os
import ffmpeg
from ffmpeg import Error as FFmpegError
from typing import List, Dict, Union
from datetime import datetime
from yt_dlp import YoutubeDL


# async def fetch_streams(link):
#     try:
#         if not link:
#             return {"success": False, "message": 'No URL entered. Kindly enter a valid URL.'}
        
#         ydl_opts = {
#             'quiet': True,
#             'no_warnings': True,
#             'simulate': True,
#             'skip_download': True,
#             'listformats': False,
#             'socket_timeout': 10,
#         }

#         # Use yt-dlp to fetch the video info
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(link, download=False)
#             if not info:
#                 raise Exception("Failed to retrieve video information.")

#         # Fetch streams concurrently using asyncio.gather to speed up the process
#         tasks = []
#         for f in info["formats"]:
#             task = asyncio.create_task(fetch_stream_details(f))
#             tasks.append(task)

        
#         streams = await asyncio.gather(*tasks)
        
#         # Sort streams by resolution in ascending order
#         #streams.sort(key=lambda x: int(x["resolution"].replace("x", "")))
    
#         for stream in streams:
#             if isinstance(stream, dict) and "video_codec" in stream:
#                 if "vp09." in stream["video_codec"]:
#                     print("supported codec:", stream)
               
#             else:
#                 print("Invalid stream format or missing 'video_codec':", stream)    


#         if not streams:
#             raise Exception("No streams available for this video.")
        
#         return {
#             'success': True,
#             'streams': streams,
#             'info': {
#                 "title": info.get("title"),
#                 "author": info.get("uploader"),
#                 "description": info.get("description"),
#                 "views": info.get("view_count", 0)
#             }
#         }

#     except Exception as e:
#         return {"success": False, "message": f'Error: {str(e)}'}
    
# async def fetch_stream_details(f):
#     """
#     Helper function to gather essential stream details
#     """
#     return {
#         "itag": f["format_id"],
#         "ext": f["ext"],
#         "resolution": f.get("resolution", "audio-only"),
#         "video_codec": f.get("vcodec", "N/A"),
#         "audio_codec": f.get("acodec", "N/A"),
#         "vbr": f.get("vbr", 0),
#         "abr": f.get("abr", 0),
#         "size_mb": await get_file_size(f)
#     }



# async def get_file_size(stream):
#     """
#     Return the file size of the stream, using filesize_approx if filesize is None.
#     Converts the size to MB for a human-readable format.
#     """
#     def parse_clen_from_url(url):
#         """
#         Extract 'clen' parameter from the URL and return its value as an integer.
#         Handles encoded query parameters within a complex URL.
#         """
#         # Decode the URL
#         decoded_url = urllib.parse.unquote(url)
        
#         # Find the 'clen' parameter in the decoded URL's path
#         clen_param = 'clen='
#         start_idx = decoded_url.find(clen_param)
#         if start_idx == -1:
#             return None
        
#         # Extract the value after 'clen='
#         start_idx += len(clen_param)
#         end_idx = decoded_url.find(';', start_idx)
#         if end_idx == -1:
#             end_idx = len(decoded_url)
        
#         # Extract 'clen' as a number
#         clen_value = decoded_url[start_idx:end_idx]
#         try:
#             return int(clen_value)  # Convert the value to an integer
#         except ValueError:
#             print(f"Invalid 'clen' value: {clen_value}")
#             return None

#     # Check for filesize or filesize_approx
#     filesize = stream.get('filesize') or stream.get('filesize_approx')

#     if filesize is None:
#         # Attempt to extract filesize from the URL
#         url = stream.get('url')
#         if not url:
#             print("No URL found in stream.")
#             return None

#         filesize = parse_clen_from_url(url)
#         if filesize is None:
#             print("No valid 'clen' parameter found.")
#             return None

#     # Convert bytes to MB
#     size_in_mb = filesize / (1024 * 1024)  # Convert bytes to MB
#     return round(size_in_mb, 3)  # Round to 3 decimal places



async def fetch_streams(link):
    try:
        if not link:
            return {"success": False, "message": "No URL entered. Kindly enter a valid URL."}

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "simulate": True,
            "skip_download": True,
            "listformats": False,
            "socket_timeout": 10,
        }

        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(link, download=False))
            if not info:
                raise Exception("Failed to retrieve video information.")

        streams = await fetch_stream_details(info["formats"])
        
        return {
            "success": True,
            "streams": streams,
            "info": {
                "title": info.get("title"),
                "artist": info.get("uploader"),
                "description": info.get("description"),
                "views": info.get("view_count", 0),
            }
        }
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


async def fetch_stream_details(formats):
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*(fetch_stream_info(session, f) for f in formats))


async def fetch_stream_info(session, f):
    return {
        "itag": f["format_id"],
        "ext": f["ext"],
        "resolution": f.get("resolution", "audio-only"),
        "video_codec": f.get("vcodec", "N/A"),
        "audio_codec": f.get("acodec", "N/A"),
        "vbr": f.get("vbr", 0),
        "abr": f.get("abr", 0),
        "size_mb": await get_file_size(session, f)
    }


async def get_file_size(session, stream):
    async def parse_clen_from_url(url):
        decoded_url = urllib.parse.unquote(url)
        clen_param = "clen="
        start_idx = decoded_url.find(clen_param)
        if start_idx == -1:
            return None

        start_idx += len(clen_param)
        end_idx = decoded_url.find(";", start_idx)
        if end_idx == -1:
            end_idx = len(decoded_url)

        clen_value = decoded_url[start_idx:end_idx]
        try:
            return int(clen_value)
        except ValueError:
            return None

    filesize = stream.get("filesize") or stream.get("filesize_approx")
    
    if filesize is None:
        url = stream.get("url")
        if not url:
            return None
        filesize = await parse_clen_from_url(url)
        if filesize is None:
            return None
    
    size_in_mb = filesize / (1024 * 1024)
    return round(size_in_mb, 3)




# async def download_stream(url, itag, start_byte=0):
#     """
#     Download a specific video stream from YouTube AND SEND IN CHUNKS TO ROUTE FN.
#     """
#     try:
#         ydl_opts = {
#             'format': itag,
#             'noplaylist': True,
#             'quiet': True,
#         }

#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             video_info = ydl.extract_info(url, download=False)
#             video_url = next(
#                 (fmt['url'] for fmt in video_info.get('formats', []) if fmt['format_id'] == itag),
#                 None
#             )
#             if not video_url:
#                 raise ValueError("Stream URL not found.")

#         headers = {'Range': f'bytes={start_byte}-'}
#         with requests.get(video_url, headers=headers, stream=True) as stream:
#             stream.raise_for_status()
#             for chunk in stream.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
#                 yield chunk

#     except Exception as e:
#         yield f"Error: {e}".encode()

async def download_stream(url, itag, start_byte=0):
    """
    Asynchronously streams a YouTube video chunk by chunk using yt-dlp.
    """
    try:
        ydl_opts = {
            'format': itag,
            'noplaylist': True,
            'quiet': True,
        }

        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            video_info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            video_url = next((fmt['url'] for fmt in video_info.get('formats', []) if fmt['format_id'] == itag), None)

            if not video_url:
                raise ValueError("Stream URL not found.")

        headers = {'Range': f'bytes={start_byte}-'}

        
        
        # Keep session open throughout
        session = aiohttp.ClientSession()
        stream = await session.get(video_url, headers=headers)
        stream.raise_for_status()

        async for chunk in stream.content.iter_any(): 
            if not isinstance(chunk, (bytes, bytearray)):  
                chunk = str(chunk).encode()

            #print(f"Sending chunk of size {len(chunk)} bytes")  
            yield chunk
        
        await session.close()  
        
    except Exception as e:
        print(f"Error streaming video: {str(e)}")
        yield b"Error: " + str(e).encode()






async def download_file(url, file_path, total_size=None):
 
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            total_size = total_size or int(response.headers.get('Content-Length', 0))
            downloaded_size = 0

            with open(file_path, 'wb') as file:
                while chunk := await response.content.read(1024 * 1024):  # 1MB chunks
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"Downloading {file_path}: {progress:.2f}% complete", end='\r')
                print()  

async def download_and_merge(url, video_itag, audio_itag):

    try:
        ydl_opts = {'noplaylist': True, 'quiet': True}

        # Get video and audio URLs
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            video_info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

        video_url = next((fmt['url'] for fmt in video_info.get('formats', []) if fmt['format_id'] == video_itag), None)
        audio_url = next((fmt['url'] for fmt in video_info.get('formats', []) if fmt['format_id'] == audio_itag), None)

        if not video_url or not audio_url:
            raise ValueError("Stream URLs not found.")

        # Get content length to determine total size
        async with aiohttp.ClientSession() as session:
            video_size = int((await session.head(video_url)).headers.get('Content-Length', 0))
            audio_size = int((await session.head(audio_url)).headers.get('Content-Length', 0))

        # Create temporary files for video and audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:

            video_path = video_file.name
            audio_path = audio_file.name

        # Download video and audio files concurrently
        print("Starting download...")
        await asyncio.gather(
            download_file(video_url, video_path, video_size),
            download_file(audio_url, audio_path, audio_size)
        )
        print("Download complete.")

        # Merge the downloaded files
        merged_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        print("Merging video and audio...")
        try:
            video_input = ffmpeg.input(video_path)
            audio_input = ffmpeg.input(audio_path)

            ffmpeg.output(
                video_input,
                audio_input,
                merged_path,
                vcodec='copy',
                acodec='aac',
                movflags='faststart',  
                strict='experimental'
            ).run(overwrite_output=True, quiet=True, capture_stdout=True, capture_stderr=True)

            print("Merging Complete...")

            # ffmpeg.output(
            #     video_input,
            #     audio_input,
            #     merged_path,
            #     vcodec='copy',
            #     acodec='aac',
            #     movflags='+faststart',  # Move moov atom to the beginning
            #     # threads=8,
            #     present = 'faster',
            #     strict='experimental',
            #     pix_fmt='yuv420p',
            # ).run(overwrite_output=True, quiet=True, capture_stdout=True, capture_stderr=True)

        except FFmpegError as e:
            print("FFmpeg stderr:", e.stderr.decode())
            raise

        # Stream or save the merged file
        with open(merged_path, 'rb') as merged_file:
            while chunk := merged_file.read(1024 * 1024):  # Stream in 1MB chunks
                yield chunk

        # Clean up temporary files
        os.remove(video_path)
        os.remove(audio_path)
        os.remove(merged_path)

    except Exception as e:
        print(f"Error during download and merge: {str(e)}")
        yield b"Error: " + str(e).encode()
        





async def get_playlist_songs(playlist_url: str) -> List[Dict[str, str]]:
    """Improved playlist extractor with better error handling"""
    loop = asyncio.get_running_loop()

    def fetch_info():
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'quiet': True,
            'no_warnings': False,
            'ignoreerrors': True,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_client': ['web', 'android'],
                    'player_skip': ['configs'],
                }
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                if not info:
                    raise ValueError("Could not extract playlist information")
                return info
        except Exception as e:
            raise RuntimeError(f"Failed to fetch playlist: {str(e)}")

    try:
        result = await loop.run_in_executor(None, fetch_info)
        
        if not result or 'entries' not in result:
            return []

        songs = []
        for entry in result['entries']:
            if not entry:  # Skip None entries
                continue
            songs.append({
                'title': entry.get('title', 'Untitled'),
                'url': entry.get('url'),
                'id': entry.get('id')
            })
        return songs

    except Exception as e:
        return e



# async def main():
#     playlist_url = input("Enter the playlist URL: ")
#     songs = await get_playlist_songs(playlist_url)
#     for song in songs:
#         print(f"{song['title']} - {song['url']}")

# asyncio.run(main())

def extract_video_info(url: str) -> Dict[str, Union[str, Dict]]:
    """Runs yt-dlp sync inside thread for 1 URL."""
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return {
            info["id"]: {
                "views": str(info.get("view_count", "?")),
                "duration": str(info.get("duration", "?")),
                "likes": str(info.get("like_count", "?")),
                "publishedAt": format_yt_date(info.get("upload_date", "Unknown")),
                # "title": info.get("title", "?"),  # Uncomment if needed
            }
        }
    except Exception as e:
        return {"error": f"yt-dlp failed: {str(e)}"}


async def get_youtube_video_details(video_urls: List[str]) -> Dict[str, Union[Dict, str]]:
    """Fetch YouTube video details in parallel using yt-dlp."""
    tasks = [asyncio.to_thread(extract_video_info, url) for url in video_urls]
    results = await asyncio.gather(*tasks)

    merged = {}
    for result in results:
        merged.update(result)
    return merged



def format_yt_date(upload_date: str) -> str:
    try:
        # Parse from "YYYYMMDD" format
        dt = datetime.strptime(upload_date, "%Y%m%d")
        # Format to "YYYY-MM-DD HH:MM:SS"
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "Unknown"



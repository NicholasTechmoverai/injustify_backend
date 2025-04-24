from pytube import Search
import requests
import logging
import os
import asyncio
logging.basicConfig(level=logging.INFO)
from typing import List, Dict, Union
from datetime import datetime
from yt_dlp import YoutubeDL
api_key = os.getenv("YOUTUBE_API_KEY")
api_available = True  # Global state to track API availability


def search_videos_pytube(query):
    """Fetch YouTube search results using PyTube."""
    try:
        logging.info("Using PyTube for YouTube search...")
        search = Search(query)

        if not search.results:
            logging.warning("No results found using PyTube.")
            return []

        return [
            {"title": video.title, 
             "url": video.watch_url,
             "Stype":'youtube'
             }
            for video in search.results
        ]
    except Exception as e:
        logging.error(f"Error in search_videos_pytube: {str(e)}")
        return []


def check_api_health():
    """Check if the YouTube API is working by making a test request."""
    global api_available
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {"part": "snippet", "q": "test", "maxResults": 1, "key": api_key}

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        api_available = True
        logging.info("YouTube API is available.")
    except requests.exceptions.RequestException:
        api_available = False
        logging.warning("YouTube API is unavailable. Switching to PyTube.")


def search_videos_yt(search_query):
    """Fetch YouTube search results using the API, fallback to PyTube on failure."""
    global api_available

    if not api_available:
        return search_videos_pytube(search_query)

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": search_query,
        "type": "video",
        "maxResults": 20,
        "key": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()
        if "items" not in data:
            raise ValueError("Invalid API response")

        return [
            {
                "title": video["snippet"]["title"],
                "url": f'https://www.youtube.com/watch?v={video["id"]["videoId"]}',
                "Stype":'youtube'
            }
            for video in data.get("items", []) if "videoId" in video.get("id", {})
        ]

    except (requests.exceptions.RequestException, ValueError) as e:
        logging.error(f"API request failed: {str(e)}. Switching to PyTube...")
        api_available = False  
        return search_videos_pytube(search_query)


check_api_health()





from googleapiclient.discovery import build

from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build

def get_video_id(video_url):
    """Extracts video ID from a YouTube URL."""
    parsed_url = urlparse(video_url)
    if parsed_url.hostname == "youtu.be":  # Shortened URL
        return parsed_url.path[1:] 
    elif parsed_url.hostname in ["www.youtube.com", "youtube.com"]:  # Standard URL
        query_params = parse_qs(parsed_url.query)
        return query_params.get("v", [None])[0]
    else:
        return None

# def get_youtube_video_details(video_url):
#     print('invoked and working!!',video_url)
#     """Fetches YouTube video details using the YouTube Data API."""

#     # Extract video ID
#     video_id = get_video_id(video_url)
#     if not video_id:
#         return {"error": "Invalid YouTube URL"}

#     # Build the YouTube API client
#     youtube = build("youtube", "v3", developerKey=api_key)

#     # Call the API to get video details
#     request = youtube.videos().list(
#         part="snippet,contentDetails,statistics",
#         id=video_id
#     )
#     response = request.execute()

#     if response["items"]:
#         video_details = response["items"][0]
        
#         title = video_details["snippet"]["title"]
#         views = video_details["statistics"]["viewCount"]
#         duration = video_details["contentDetails"]["duration"]
#         likes = video_details["statistics"].get("likeCount")  

#         return{
#             "success":True,
#             "info":{
#                 "title": title,
#                 "views": views,
#                 "duration": duration,
#                 "likes": likes if likes else "Not available",
#                 }
#         }

#     else:
#         return {"error": "Video not found or invalid URL"}







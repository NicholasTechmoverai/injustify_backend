
from googleapiclient.discovery import build

from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build


api_key = ""


def get_video_id(video_url):
    """Extracts video ID from a YouTube URL."""
    parsed_url = urlparse(video_url)
    if parsed_url.hostname == "youtu.be":  # Shortened URL
        return parsed_url.path[1:]  # Remove the leading "/"
    elif parsed_url.hostname in ["www.youtube.com", "youtube.com"]:  # Standard URL
        query_params = parse_qs(parsed_url.query)
        return query_params.get("v", [None])[0]
    else:
        return None

def get_youtube_video_details(video_url):
    print('invoked and working!!',video_url)
    """Fetches YouTube video details using the YouTube Data API."""
    # Your API key from Google Cloud Console

    # Extract video ID
    video_id = get_video_id(video_url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}

    # Build the YouTube API client
    youtube = build("youtube", "v3", developerKey=api_key)

    # Call the API to get video details
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id
    )
    response = request.execute()
    #print(response)

    # Extract relevant details
    if response["items"]:
        video_details = response["items"][0]
        
        # Extracting details from the response
        title = video_details["snippet"]["title"]
        views = video_details["statistics"]["viewCount"]
        duration = video_details["contentDetails"]["duration"]
        likes = video_details["statistics"].get("likeCount")  # Only if provided
        dislikes = "Not available"  # YouTube no longer provides dislikeCount publicly

        return{
            "success":True,
            "info":{
                "title": title,
                "views": views,
                "duration": duration,
                "likes": likes if likes else "Not available",
                "dislikes": dislikes,
                }
        }

    else:
        return {"error": "Video not found or invalid URL"}

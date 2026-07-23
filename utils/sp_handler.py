import spotipy,json,os
import asyncio

from spotipy.oauth2 import SpotifyClientCredentials
client_id = os.getenv('SPOTIPY_CLIENT_ID', 'mock_spotify_client_id')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET', 'mock_spotify_client_secret')

try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id, client_secret))
except Exception:
    sp = None

async def Search_suggestions_spotify(search):
    try:
        results = await asyncio.to_thread(sp.search, q=search, type="track", limit=10)
        #print(results)
        
        suggestions = [
            {"name": track['name'], "artist": track['artists'][0]['name']}
            for track in results['tracks']['items']
        ]
        return suggestions
    except Exception as e:
        print(f"Error in Spotify search: {str(e)}")
        return []



def search_songs_spotify(query):
    """Fetch Spotify search results for a given query."""
    try:
        #print("Searching Spotify... 🎶")

        results = sp.search(q=query, limit=10, type='track')
        #print(json.dumps(results,indent=4))
        songs = [
            {
                "title": track["name"],
                "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                "url": track["external_urls"]["spotify"]
            }
            for track in results["tracks"]["items"]
        ]
        return songs
    except Exception as e:
        print(f"Error in search_songs_spotify: {str(e)}")
        return []





"""
async def main():
    suggestions = await Search_suggestions_spotify("london")
    print(suggestions)

asyncio.run(main())"""

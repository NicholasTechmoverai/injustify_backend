import logging
import uuid
import mysql.connector
from config import Config
logging.basicConfig(level=logging.INFO)
from config import Config
import aiomysql


async def likeUnlike(songId, userId):
    if not songId or not userId:
        return {"success": False, "message": "Invalid song or user ID"}

    sql_unlike = "DELETE FROM songlikes WHERE song_id = %s AND user_id = %s"
    sql_insert = "INSERT INTO songlikes (song_id, user_id) VALUES (%s, %s)"

    values = (songId, userId)

    try:
        conn = await Config.get_db_connection()
        if not conn:
            return {"success": False, "message": "Database connection failed"}

        async with conn.cursor() as cursor:
            # First, attempt to delete (unlike)
            await cursor.execute(sql_unlike, values)
            if cursor.rowcount > 0:
                action_message = "Unliked successfully!"
            else:
                # If nothing was deleted, insert (like)
                await cursor.execute(sql_insert, values)
                action_message = "Liked successfully!"

            await conn.commit()

            # Get updated like count
            sql_count = "SELECT COUNT(*) FROM songlikes WHERE song_id = %s"
            await cursor.execute(sql_count, (songId,))
            likes_Res = await cursor.fetchone()
            likes = likes_Res[0] if likes_Res else 0

            return {
                "success": True,
                "message": action_message,
                "newUpdate": likes
            }

    except Exception as err:
        print(f"Error liking/unliking song: {err}")
        return {"success": False, "message": "Failed to like/unlike song!"}

    finally:
        if conn:
            try:
                if conn in Config.pool._used:
                    await Config.pool.release(conn)
            except Exception as e:
                print(f"Error releasing connection: {e}")

async def update_view_count(songId, userId, songPercentage):
    """
    Async function to update the view count for a song effectively.
    """
    if not songId or not userId or songPercentage is None:
        print(f"⚠️ Missing required data: songId={songId}, userId={userId}, progress={songPercentage}")
        return {"success": False, "message": "Missing required parameters"}

    try:
        conn = await Config.get_db_connection()
        if not conn:
            return {"success": False, "message": "Database connection failed"}

        async with conn.cursor() as cursor:
            sql_check = "SELECT id, view_count, progress FROM views WHERE song_id = %s AND user_id = %s"
            await cursor.execute(sql_check, (songId, userId))
            existing_view = await cursor.fetchone()

            if existing_view:
                view_id, view_count, last_progress = existing_view

                if last_progress >= 98 and songPercentage < 10:
                    sql_reset_progress = """
                        UPDATE views 
                        SET progress = %s, last_viewed = NOW()
                        WHERE song_id = %s AND user_id = %s
                    """
                    await cursor.execute(sql_reset_progress, (songPercentage, songId, userId))

                elif last_progress < 50 and songPercentage >= 50:
                    sql_update_view = """
                        UPDATE views 
                        SET progress = %s, view_count = view_count + 1, last_viewed = NOW()
                        WHERE song_id = %s AND user_id = %s
                    """
                    await cursor.execute(sql_update_view, (songPercentage, songId, userId))

                else:
                    sql_update_progress = """
                        UPDATE views 
                        SET progress = %s, last_viewed = NOW()
                        WHERE song_id = %s AND user_id = %s
                    """
                    await cursor.execute(sql_update_progress, (songPercentage, songId, userId))

            else:
                viewCount = 1 if songPercentage >= 50 else 0
                sql_insert = """
                    INSERT INTO views (user_id, song_id, view_count, progress) 
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        view_count = VALUES(view_count), 
                        progress = VALUES(progress)
                """
                await cursor.execute(sql_insert, (userId, songId, viewCount, songPercentage))


            await conn.commit()
            return {"success": True, "message": "View count updated successfully"}

    except aiomysql.Error as db_err:
        print(f"Database error: {db_err}")
        return {"success": False, "message": str(db_err)}

    except Exception as err:
        print(f"Unexpected error: {err}")
        return {"success": False, "message": str(err)}

    finally:
        if conn:
            try:
                if conn in Config.pool._used:
                    await Config.pool.release(conn) 
            except Exception as e:
                print(f"Error releasing connection: {e}")

async def insert_download(
    user_id, song_id, file_name=None, file_format=None, itag=None,
    file_size=None, file_source=None, thumbnail=None,
    user_agent=None, is_partial=False, downloaded_size=None,
    download_status='IN_PROGRESS', **optional_updates
):
    """Insert or update a download record with dynamic fields."""
    try:
        conn = await Config.get_db_connection()
        if not conn:
            return {"success": False, "message": "Database connection failed"}
        

        if isinstance(file_size, (list, tuple)) and len(file_size) == 1:
             file_size = file_size[0]


        async with conn.cursor() as cursor:
            # Required keys
            base_columns = ["user_id", "song_id", "itag"]
            base_values = [user_id, song_id, itag]

            insert_columns = []
            insert_values = []

            if file_name is not None:
                insert_columns.append("file_name")
                insert_values.append(file_name)

            if file_format is not None:
                insert_columns.append("file_format")
                insert_values.append(file_format)

            if file_size is not None:
                insert_columns.append("file_size")
                insert_values.append(file_size)

            if file_source is not None:
                insert_columns.append("file_source")
                insert_values.append(file_source)

            if thumbnail is not None:
                insert_columns.append("thumbnail")
                insert_values.append(thumbnail)

            if user_agent is not None:
                insert_columns.append("user_agent")
                insert_values.append(user_agent)

            if downloaded_size is not None:
                insert_columns.append("downloaded_size")
                insert_values.append(downloaded_size)

            if download_status is not None:
                insert_columns.append("download_status")
                insert_values.append(download_status)

            # Always insert is_partial
            insert_columns.append("is_partial")
            insert_values.append(is_partial)

            # Allowed fields for update
            allowed_updates = {
                "file_name", "file_format", "file_size", "file_source",
                "thumbnail", "user_agent", "downloaded_size", "is_partial", "download_status"
            }

            update_fields = []
            update_values = []

            # Add fields from optional_updates
            for key, val in optional_updates.items():
                if key in allowed_updates:
                    update_fields.append(f"{key} = %s")
                    update_values.append(val)

            # Add explicitly passed fields (if not already in optional_updates)
            for col, val in zip(insert_columns, insert_values):
                if col in allowed_updates and col not in optional_updates:
                    update_fields.append(f"{col} = %s")
                    update_values.append(val)

            all_columns = base_columns + insert_columns
            placeholders = ["%s"] * len(all_columns)
            all_values = base_values + insert_values

            update_clause = ", ".join(update_fields) if update_fields else "download_status = download_status"

            # DEBUG: Print the full insert and update values
            print("DEBUG: Insert columns and values:")
            for col, val in zip(all_columns, all_values):
                print(f"  {col}: {val}")

            print("DEBUG: Update fields and values:")
            for field, val in zip(update_fields, update_values):
                print(f"  {field}: {val}")

            query = f"""
                INSERT INTO downloads ({", ".join(all_columns)})
                VALUES ({", ".join(placeholders)})
                ON DUPLICATE KEY UPDATE {update_clause}
            """

            await cursor.execute(query, all_values + update_values)
            await conn.commit()

            return {"success": True, "message": "Inserted or updated download"}

    except Exception as e:
        print(f"Error inserting/updating download: {e}")
        return {"success": False, "message": str(e)}

    finally:
        if conn:
            await Config.pool.release(conn)




async def fetch_songs(user_id=None, songs_per_page=15, offset=0, search=None, songId=None):
    """Async function to fetch songs from the database."""
    try:
        conn = await Config.get_db_connection()
        if not conn:
            return {"success": False, "message": "Database connection failed"}

        async with conn.cursor() as cursor:
            base_query = """
                SELECT 
                    injustifyMusic.song_id, 
                    artist, 
                    title, 
                    url, 
                    thumbnail_path, 
                    duration, 
                    views, 
                    upload_date,
                    (SELECT COUNT(*) FROM songlikes WHERE songlikes.song_id = injustifyMusic.song_id) AS likes,
                    EXISTS(
                        SELECT 1 
                        FROM songlikes 
                        WHERE songlikes.song_id = injustifyMusic.song_id AND songlikes.user_id = %s
                    ) AS liked
                FROM injustifyMusic
            """
            values = [user_id] if user_id else [None]

            # Case: Fetch specific song by songId
            if songId:
                sql_query = f"{base_query} WHERE injustifyMusic.song_id = %s"
                values.append(songId)
                await cursor.execute(sql_query, tuple(values))

            # Case: Search songs by title or artist
            elif search and search.lower() != 'null':
                sql_query = f"""
                    {base_query}
                    WHERE title LIKE %s OR artist LIKE %s
                    ORDER BY title
                    LIMIT %s OFFSET %s
                """
                search_filter = f"%{search}%"
                values.extend([search_filter, search_filter, songs_per_page, offset])
                await cursor.execute(sql_query, tuple(values))

            # Default: fetch paginated songs
            else:
                sql_query = f"{base_query} ORDER BY title LIMIT %s OFFSET %s"
                values.extend([songs_per_page, offset])
                await cursor.execute(sql_query, tuple(values))

            songs = await cursor.fetchall()

            result = [
                {
                    "song_id": song[0],
                    "artist": song[1],
                    "title": song[2],
                    "url": f"{song[3]}",
                    "thumbnail": f"{Config.thumbnailPath}/{song[4]}",
                    "duration": song[5],
                    "views": song[6],
                    "date": song[7].strftime('%Y-%m-%d %H:%M:%S') if song[7] else None,
                    "likes": song[8],
                    "liked": bool(song[9]),
                    "Stype": "injustify"
                }
                for song in songs
            ]

            return {"success": True, "songs": result}

    except Exception as e:
        return {"success": False, "message": "Error fetching songs", "error": str(e)}

    finally:
        try:
            if conn and conn in Config.pool._used:
                await Config.pool.release(conn)
        except Exception as e:
            print("Failed to release connection:", str(e))




async def get_playlist_songs(playlist_id):
    """
    Async function to fetch songs from a playlist. If the playlist ID is 3031 or 7522,
    it fetches 20 random songs from the `injustifyMusic` database.
    """
    try:
        conn = await Config.get_db_connection()
        if not conn:
            return {"success": False, "message": "Database connection failed"}
        
        async with conn.cursor() as cursor:
            if playlist_id in {'3031', '7522'}:  # Fetch random songs for these IDs
                sql_query = """
                    SELECT song_id, title, artist, url, thumbnail_path
                    FROM injustifyMusic
                    ORDER BY RAND()
                    LIMIT 20;
                """
                await cursor.execute(sql_query)
                songs = await cursor.fetchall()
                
                return {
                    "success": True,
                    "playlist_name": "Random Playlist",
                    "playlistId": playlist_id,
                    "songs": [
                        {
                            "song_id": song[0],
                            "title": song[1],
                            "artist": song[2],
                            "url": song[3],
                            "thumbnail": f"{Config.thumbnailPath}/{song[4]}",
                            "Stype": "injustify"
                        } for song in songs
                    ]
                }
            
            # Fetch songs for a specific playlist
            sql_query = """
                SELECT ps.song_id, im.title, im.artist, im.url, im.thumbnail_path, p.name 
                FROM playlistSongs ps 
                JOIN injustifyMusic im ON ps.song_id = im.song_id 
                JOIN playlists p ON ps.playlist_id = p.playlist_id 
                WHERE ps.playlist_id = %s;
            """
            await cursor.execute(sql_query, (playlist_id,))
            songs = await cursor.fetchall()
            
            if not songs:
                return {"playlist_name": None, "songs": []}
            
            return {
                "playlist_name": songs[0][5],
                "playlistId": playlist_id,
                "songs": [
                    {
                        "song_id": song[0],
                        "title": song[1],
                        "artist": song[2],
                        "url": song[3],
                        "thumbnail": f"{Config.thumbnailPath}/{song[4]}",
                        "Stype": "injustify"
                    } for song in songs
                ]
            }
    
    except Exception as e:
        return {"success": False, "message": "Error fetching playlist songs", "error": str(e)}
    
    finally:
        if conn:
            await Config.pool.release(conn)  



async def fetchTrendingSongs(userId=None):
    """
    Fetch trending songs based on views, likes, and comments within the last 30 days.

    Criteria: JUST FOR DEVELOPMENT
    - Songs viewed by at least 5 unique users in the past 30 days.
    - Songs with at least 5 comments in the past 30 days.
    - Songs with engagement ranked by:
      1. Average progress percentage.
      2. Number of likes.
      3. Number of comments.
    """

    sql_query = """
        SELECT 
            s.song_id, 
            s.title, 
            s.artist, 
            s.thumbnail_path,
            s.upload_date, 
            AVG(v.progress) AS average_progress,
            COUNT(DISTINCT l.user_id) AS likes_count,
            COUNT(DISTINCT c.comment_id) AS comments_count
            CASE 
                WHEN EXISTS (
                    SELECT 1 
                    FROM songlikes 
                    WHERE songlikes.song_id = s.song_id AND songlikes.user_id = %s
                ) THEN TRUE 
                ELSE FALSE 
            END AS liked
        FROM injustifymusic s
        JOIN views v ON s.song_id = v.song_id
        LEFT JOIN songlikes l ON s.song_id = l.song_id AND l.like_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
        LEFT JOIN comments c ON s.song_id = c.songId AND c.created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
        WHERE v.last_viewed >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
        GROUP BY s.song_id, s.title, s.artist, s.thumbnail_path, s.upload_date
        HAVING COUNT(DISTINCT v.user_id) >= 1 AND COUNT(DISTINCT c.comment_id) >= 1
        ORDER BY average_progress DESC, likes_count DESC, comments_count DESC
    """

    try:
        conn = await Config.get_db_connection()
        if not conn:
            return {"success": False, "message": "Database connection failed"}

        async with conn.cursor() as cursor:
            await cursor.execute(sql_query,userId)
            trending_songs = await cursor.fetchall() 

        trending_songs_list = [
            {
                'id': song[0],
                'title': song[1],
                'artist': song[2],
                'thumbnail': f"{Config.thumbnailPath}/{song[3]}",
                'upload_date': song[4].strftime('%Y-%m-%d'),
                'average_progress': song[5],
                'likes_count': song[6],
                'comments_count': song[7],
                'liked': song[8],
                'Stype': "injustify"  
            }
            for song in trending_songs
        ]

        return {"success": True, "feed": trending_songs_list}

    except Exception as e:
        print(f"Error fetching trending songs: {e}")
        return {"success": False, "message": "An error occurred while fetching trending songs"}

    finally:
        if conn:
            await Config.pool.release(conn) 

async def fetch_User_LikedSongs(userId, offset=0, limit=20):
    """
    Fetch songs liked by a user, sorted in descending order (recently liked),
    with pagination (10 per fetch by default). Converts tuples to dictionaries.
    """
    print(f"Fetching liked songs for user: {userId}")

    sql_query = """
        SELECT 
            s.song_id, 
            s.title, 
            s.artist, 
            s.thumbnail_path AS album_cover, 
            s.release_date, 
            l.like_date
        FROM injustifymusic s
        JOIN songlikes l ON s.song_id = l.song_id
        WHERE l.user_id = %s
        ORDER BY l.like_date DESC
        LIMIT %s OFFSET %s
    """
    values = (userId, limit, offset)

    try:
        conn = await Config.get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(sql_query, values)
            liked_songs = await cursor.fetchall()

        liked_songs_list = [
            {
                "song_id": song[0],
                "title": song[1],
                "artist": song[2],
                "thumbnail": f'{Config.thumbnailPath}/{song[3]}',
                "release_date": song[4].strftime('%Y-%m-%d') if song[4] else None,
                "like_date": song[5].strftime('%Y-%m-%d %H:%M:%S') if song[5] else None,
                "liked":True,
                "Stype": "injustify" 
            }
            for song in liked_songs
        ]

        return {"success": True, "feed": liked_songs_list}

    except aiomysql.MySQLError as err:
        print(f"Error fetching liked songs: {err}")
        return {"success": False, "message": "Failed to fetch liked songs!"}

    finally:
        if conn:
            await Config.pool.release(conn) 


async def fetchUserTopSongs(userId, limit=10):
    """
    Fetch top songs based on how many times a specific user has viewed them.
    """
    print(f"Fetching top songs for user: {userId}")

    sql_query = """
        SELECT 
            s.song_id, 
            s.title, 
            s.artist, 
            s.thumbnail_path AS album_cover, 
            s.release_date,
            COALESCE(v.view_count, 0) AS user_view_count,  -- Ensure 0 if no views exist
            COALESCE(l.liked, FALSE) AS liked  -- Ensure FALSE if not liked
        FROM injustifymusic s
        LEFT JOIN views v ON s.song_id = v.song_id AND v.user_id = %s
        LEFT JOIN (
            SELECT song_id, TRUE AS liked 
            FROM songlikes 
            WHERE user_id = %s
        ) l ON s.song_id = l.song_id
        ORDER BY COALESCE(v.view_count, 0) DESC 
        LIMIT %s
    """
    values = (userId, userId, limit)


    try:
        conn = await Config.get_db_connection()  
        async with conn.cursor() as cursor:
            await cursor.execute(sql_query, values)
            top_songs = await cursor.fetchall()

        top_songs_list = [
            {
                "song_id": song[0],
                "title": song[1],
                "artist": song[2],
                "thumbnail": f'{Config.thumbnailPath}/{song[3]}',  
                "release_date": song[4].strftime('%Y-%m-%d') if song[4] else None,
                "user_view_count": song[5],
                "liked": song[6],
                "Stype": "injustify",
            }
            for song in top_songs
        ]

        return {"success": True, "feed": top_songs_list}

    except aiomysql.MySQLError as err:
        print(f"Error fetching top songs: {err}")
        return {"success": False, "message": "Failed to fetch top songs!"}

    finally:
        if conn:
            await Config.pool.release(conn)  


async def fetchStreamRate(userId):
    """
    Fetch stream rate for 10 users surrounding the given userId, including user info.
    Prevents negative ranking issues.
    """
    print(f"Fetching stream rate for user: {userId}")

    try:
        conn = await Config.get_db_connection()  
        if not conn:
            return {"success": False, "message": "Database connection failed"}

        sql_query = """
            WITH user_activity AS (
                SELECT 
                    v.user_id,
                    COUNT(*) AS total_views,
                    COUNT(DISTINCT v.song_id) AS unique_songs,
                    AVG(v.progress) AS avg_completion,
                    SUM(v.view_count) AS total_view_count,
                    MAX(v.last_viewed) AS last_active
                FROM injustify.views v
                GROUP BY v.user_id
            ), ranking_data AS (
                SELECT 
                    ua.user_id,
                    ua.total_views,
                    ua.unique_songs,
                    ua.avg_completion,
                    ua.total_view_count,
                    DATEDIFF(NOW(), ua.last_active) AS days_since_active,
                    (ua.total_view_count * 0.5 + ua.unique_songs * 0.3 + ua.avg_completion * 0.2) 
                    / (1 + DATEDIFF(NOW(), ua.last_active) * 0.05) AS engagement_score
                FROM user_activity ua
            ), ranked_users AS (
                SELECT 
                    rd.user_id, 
                    u.name,
                    u.picture,
                    RANK() OVER (ORDER BY rd.engagement_score DESC) AS global_rank,
                    rd.engagement_score,
                    rd.total_views,
                    rd.unique_songs,
                    rd.avg_completion
                FROM ranking_data rd
                JOIN injustify.injustifyusers u ON rd.user_id = u.id
            ), user_position AS (
                SELECT global_rank FROM ranked_users WHERE user_id = %s
            )
            SELECT * FROM ranked_users 
            WHERE global_rank BETWEEN 
                CASE 
                    WHEN (SELECT global_rank FROM user_position) > 5 
                    THEN (SELECT global_rank FROM user_position) - 5 
                    ELSE 1  -- If user is in the top 5, start from rank 1
                END
            AND 
                CASE 
                    WHEN (SELECT global_rank FROM user_position) > 5 
                    THEN (SELECT global_rank FROM user_position) + 5 
                    ELSE (SELECT global_rank FROM user_position) + (5 + (5 - (SELECT global_rank FROM user_position))) 
                    -- This ensures we get 10 users in total by shifting the upper bound higher
                END
            ORDER BY global_rank;
        """

        async with conn.cursor() as cursor:
            await cursor.execute(sql_query, (userId,))  
            stream_rate = await cursor.fetchall() 
        if stream_rate:
            return {
                "success": True,
                "stream_rate": [
                    {
                        "userId": row[0],
                        "username": row[1],
                        "profile_image_url": f"{Config.profilePath}/{row[2]}",
                        "global_rank": row[3],
                        "engagement_score": row[4],
                        "total_views": row[5],
                        "unique_songs": row[6],
                        "avg_completion": row[7]
                    }
                    for row in stream_rate
                ]
            }
        
        return {"success": True, "stream_rate": []}

    except Exception as e:
        print(f"Error fetching stream rate: {e}")
        return {"success": False, "message": "An error occurred while fetching stream rate"}

    finally:
        if conn:
            await Config.pool.release(conn) 


async def createPlaylistDB(playlistName, userId):
    print(f"Creating playlist {playlistName} with user {userId}")
    playlist_id = f"pl{str(uuid.uuid4())[:8]}"
    sql_query = "INSERT INTO playlists (playlist_id, name, created_by) VALUES (%s, %s, %s)"
    values = (playlist_id, playlistName, userId)

    conn = None
    try:
        conn = await Config.get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(sql_query, values)
            await conn.commit()
            return {
                "success": True,
                "message": "Playlist created successfully 😊",
                "info": {
                    "id": playlist_id,
                    "playlistName": playlistName,
                    "created_by": userId,
                    "type": "local"
                }
            }
    except Exception as err:
        print(f"Error creating playlist: {err}")
        return {"success": False, "message": "Error creating playlist!!"}
    finally:
        if conn:
            await Config.pool.release(conn) 


async def updatePlaylistDB(playlistId, songId, action, newPlaylistName=None):
    print(f"Updating playlist {playlistId}, songId: {songId}, action: {action}, newPlaylistName: {newPlaylistName}")

    conn = None
    try:
        conn = await Config.get_db_connection()
        async with conn.cursor() as cursor:
            
            # ADD SONG TO PLAYLIST
            if action == "add":
                sql_query = """
                INSERT INTO playlistSongs (playlist_id, song_id) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE song_id = song_id
                """  
                await cursor.execute(sql_query, (playlistId, songId))
                await conn.commit()

                success_message = "Song added successfully!"

            # REMOVE SONG FROM PLAYLIST
            elif action == "remove":
                sql_query = "DELETE FROM playlistSongs WHERE playlist_id = %s AND song_id = %s"
                await cursor.execute(sql_query, (playlistId, songId))
                await conn.commit()

                success_message = "Song removed successfully!"

            # DELETE ENTIRE PLAYLIST
            elif action == "delete":
                sql_query = "DELETE FROM playlistSongs WHERE playlist_id = %s"
                await cursor.execute(sql_query, (playlistId,))
                await conn.commit()

                sql_queryv = "DELETE FROM playlists WHERE playlist_id = %s"
                await cursor.execute(sql_queryv, (playlistId,))
                await conn.commit()
                

                success_message = "Playlist deleted successfully!"

            # RENAME PLAYLIST
            elif action == "rename":
                if not newPlaylistName:
                    return {"success": False, "message": "New playlist name is required for renaming."}
                sql_query = "UPDATE playlists SET name = %s WHERE playlist_id = %s"
                await cursor.execute(sql_query, (newPlaylistName, playlistId))
                await conn.commit()

                success_message = "Playlist renamed successfully!"


            else:
                return {"success": False, "message": f"Invalid action: {action}"}

            return {"success": True, "message": success_message}

    except aiomysql.Error as db_err:
        print(f"Database error: {db_err}")
        if conn:
            await conn.rollback() 
        return {"success": False, "message": "Database error occurred!"}

    except Exception as err:
        print(f"Unexpected error: {err}")
        if conn:
            await conn.rollback()
        return {"success": False, "message": f"Failed to {action} playlist!"}

    finally:
        if conn:
            Config.pool.release(conn)  


    



async def get_playlists(user_id):
    if not user_id:
        return {"success": False, "message": "User ID is required"}

    conn = None  
    try:
        conn = await Config.get_db_connection()
        async with conn.cursor() as cursor:
            sql_query = """
                SELECT p.playlist_id, p.name, p.description, p.created_by, p.created_at, u.Picture,
                    (SELECT COUNT(*) FROM playlistSongs WHERE playlist_id = p.playlist_id) AS song_count
                FROM playlists p
                LEFT JOIN injustifyusers u ON p.created_by = u.id
                WHERE p.created_by = %s
            """
            await cursor.execute(sql_query, (user_id,))
            playlists = await cursor.fetchall()

        if playlists:
            return {
                "success": True,
                "playlists": [
                    {
                        "id": p[0], 
                        "name": p[1], 
                        "description": p[2],
                        "created_by": p[3],
                        "created_at": p[4].strftime('%Y-%m-%d %H:%M:%S') if p[4] else None,
                        "picture": f"{Config.profilePath}/{p[5]}" if p[5] else None, 
                        "song_count": p[6]
                    }
                    for p in playlists
                ]
            }

        return {"success": False, "message": "No playlists found for this user", "playlists": []}

    except aiomysql.Error as db_err: 
        print(f"Database Error: {db_err}")
        return {"success": False, "message": "Database error occurred!", "error": str(db_err)}

    except Exception as err:
        print(f"Unexpected Error: {err}")
        return {"success": False, "message": "An error occurred while fetching playlists", "error": str(err)}

    finally:
        if conn:  
            Config.pool.release(conn)

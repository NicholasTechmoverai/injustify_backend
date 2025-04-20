import logging,os
import uuid
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config
from datetime import datetime
from typing import Optional, List, Dict, Union
import logging
import aiofiles
from werkzeug.utils import secure_filename
logging.basicConfig(level=logging.INFO)
import base64


async def fetch_user(user_id):
    if not user_id:
        return {"success": False, "message": "User ID is required"}
    
    select = 'email' if '@' in user_id and '.' in user_id else 'id'
    
    conn = await Config.get_db_connection()
    try:
        async with conn.cursor() as cursor:
            query = f"SELECT * FROM injustifyUsers WHERE {select} = %s"
            await cursor.execute(query, (user_id,))
            user = await cursor.fetchone()
            
            if user:
                userD = {
                    'success': True,
                    "id": user[1],
                    "email": user[0],
                    "name": user[2],
                    "picture": f"{Config.profilePath}/{user[3]}",
                    "verified_email": user[4],
                    "created_at": user[6].strftime('%Y-%m-%d %H:%M:%S'),
                }
                return {"success": True, "message": "User found", "user_info": userD}
            else:
                return {"success": False, "message": "User not found"}
    except Exception as err:
        logging.error("Error: %s", err)
        return {"success": False, "error": "An unexpected error occurred"}
    finally:
        if conn:
            Config.pool.release(conn)

async def validate_user_login(email, password):
    conn = await Config.get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT email, password FROM injustifyUsers WHERE email = %s", (email,))
            user = await cursor.fetchone()
            
            if user is None:
                return {"userFound": False}
            
            db_email, db_password = user
            if check_password_hash(db_password, password):
                user_info = await fetch_user(db_email)
                return {"user_info": user_info, "userFound": True, "truepassword": True}
            
            return {"user_info": None, "userFound": True, "truepassword": False}
    except Exception as err:
        logging.error("Error validating user login: %s", err)
        return {"error": "An error occurred during login validation"}
    finally:
        if conn:
            Config.pool.release(conn)


async def validate_user(user_email):
    try:
        conn = await Config.get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT verified_email FROM injustifyUsers WHERE email = %s",
                (user_email,)
            )
            user = await cursor.fetchone()
            
            return user is not None and user[0] == 1
    except Exception as err:
        logging.error("Error validating user: %s", err)
        return False
    finally:
        if conn:
            await Config.pool.release(conn)  

async def create_new_user(Userinfo):
    if not Userinfo:
        return 'error'
    
    id = Userinfo.get('id', str(uuid.uuid4()))
    name = Userinfo['name']
    email = Userinfo['email']
    password = generate_password_hash(Userinfo.get('password', '')) if Userinfo.get('password') else None
    profilePicture = Userinfo.get('picture', 'nouser.jpeg')
    verified_email = Userinfo.get('verified_email', False)
    
    conn = await Config.get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO injustifyUsers (id, email, name, password, picture, verified_email) VALUES (%s, %s, %s, %s, %s, %s)",
                (id, email, name, password, profilePicture, verified_email)
            )
            await conn.commit()
            return 'success'
    except Exception as err:
        logging.error("Error: %s", err)
        return str(err)
    finally:
        if conn:
            Config.pool.release(conn)

async def update_user_password(username, password):
    if not username or not password:
        return {"success": False, "message": "Username and password are required"}
    
    password_hash = generate_password_hash(password)
    try:
        conn = await Config.get_db_connection()

        async with conn.cursor() as cursor:
            query = "UPDATE injustifyUsers SET password = %s WHERE email = %s"
            await cursor.execute(query, (password_hash, username))
            await conn.commit()
            affected_rows = cursor.rowcount
            
            if affected_rows == 0:
                return {"success": False, "message": "No user found with that email"}
            return {"success": True, "message": "Password updated successfully"}
    except Exception as db_err:
        logging.error("Database Error: %s", db_err)
        return {"success": False, "message": f"Database error: {str(db_err)}"}
    finally:
        if conn:
            Config.pool.release(conn)


async def fetch_downloads(
    user_id: Optional[int] = None,
    song_id: Optional[str] = None,
    name: Optional[str] = None,
    date: Optional[Union[str, datetime]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: Optional[str] = None
) -> Optional[List[Dict]]:
    """
    Fetch downloads from the database with flexible filtering, sorting, and pagination.
    """
    conn = await Config.get_db_connection()
    try:
        async with conn.cursor() as cursor:
            query = "SELECT * FROM downloads WHERE 1=1"
            values = []

            if user_id:
                if '@' in user_id and '.' in user_id:
                    qr = "SELECT id FROM injustifyusers WHERE email = %s"
                    await cursor.execute(qr, (user_id,))
                    result = await cursor.fetchone()
                    if result:
                        user_id = result[0]

                query += " AND user_id = %s"
                values.append(user_id)
            
            if song_id:
                query += " AND song_id = %s"
                values.append(song_id)
            
            if name:
                query += " AND file_name LIKE %s"
                values.append(f"%{name}%")
            
            if date:
                query += " AND DATE(timestamp) = %s"
                values.append(date)
            
            if order_by:
                query += f" ORDER BY {order_by}"
            
            if limit is not None:
                query += " LIMIT %s"
                values.append(limit)
            
            if offset is not None:
                query += " OFFSET %s"
                values.append(offset)

            await cursor.execute(query, values)
            results = await cursor.fetchall()

            downloads = [{

                'download_id':result[0],
                'user_id': result[1],
                'song_id': result[2],
                'itag':result[5],
                'file_source':result[7],
                'filesize': result[6],
                'filename': result[3],
                'thumbnail': result[14] if 'injustify' not in result[7] else f"{Config.thumbnailPath}/{result[14]}",
                'links': result[2],
                'timestamp': result[10].strftime('%Y-%m-%d %H:%M:%S'),
            } for result in results]
            
            return {"success": True, "downloads": downloads}
    
    except Exception as e:
        logging.error(f"Error fetching downloads: {e}")
        return {"success": False, "downloads": []}
    
    finally:
        if conn:
            await Config.pool.release(conn)  


async  def delete_song_from_downloads(songId,userId):
    conn = await Config.get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("DELETE FROM downloads WHERE user_id=%s AND song_id=%s", (userId, songId))
            await conn.commit()
            return {"success": True, "message": "Song deleted successfully."}
    except Exception as e:
        logging.error(f"Error deleting song from downloads: {e}")
        return {"success": False, "message": f"Error deleting song: {str(e)}"}
    finally:
        if conn:
            await Config.pool.release(conn) 





async def update_UserProfile(userId, username=None, email=None, picture=None):

    print("Updating user profile for user " , userId ,"...", picture)
    if not userId:
        return {"success": False, "message": "User ID is required."}

    update_query = []
    params = []
    picture_path = None

    if username:
        update_query.append("name=%s")
        params.append(username)

    if email:
        update_query.append("email=%s")
        params.append(email)


    if picture:
        try:
            filename = f"user_{userId}.png"
            picture_path = os.path.join(Config.PROFILE_UPLOAD_FOLDER, filename)
            

            if isinstance(picture, str) and picture.startswith("data:image"): 
                image_data = picture.split(",")[1]
                async with aiofiles.open(picture_path, "wb") as img_file:
                    await img_file.write(base64.b64decode(image_data))

            elif hasattr(picture, "filename"):  
                filename = secure_filename(filename)
                async with aiofiles.open(picture_path, "wb") as img_file:
                    await img_file.write(await picture.read())

            update_query.append("picture=%s")
            params.append(filename)

        except Exception as e:
            logging.error(f"Failed to process image: {e}")
            return {"success": False, "message": f"Failed to process image: {str(e)}"}

    if not update_query:
        return {"success": False, "message": "No updates provided."}

    update_query_str = ", ".join(update_query)
    params.append(userId)

    sql_query = f"UPDATE injustifyusers SET {update_query_str} WHERE id=%s"

    try:
        conn = await Config.get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(sql_query, params)
            await conn.commit()

        updated_user = await fetch_user(userId)    
               
        return {"success": True, "message": "Profile updated successfully.","user":updated_user.get("user_info")}
    except Exception as err:
        logging.error(f"Error updating user profile: {err}")
        return {"success": False, "message": "Failed to update profile."}
    finally:
        if conn:
            await Config.pool.release(conn)


async def delete_user(userId, password):
    conn = await Config.get_db_connection()
    try:
        async with conn.cursor() as cursor:
            # Validate password
            query = "SELECT password FROM injustifyusers WHERE id=%s"
            await cursor.execute(query, (userId,))
            result = await cursor.fetchone()
            if not result or not check_password_hash(result[0], password):
                return {"success": False, "message": "Invalid password."}

            # Delete from playlistsongs
            query = """
                DELETE FROM playlistsongs
                WHERE playlist_id IN (
                    SELECT playlist_id FROM playlists WHERE created_by = %s
                );
            """
            await cursor.execute(query, (userId,))
            await conn.commit()

            # Delete from playlists
            query = "DELETE FROM playlists WHERE created_by = %s"
            await cursor.execute(query, (userId,))
            await conn.commit()

            # Delete from downloads
            query = "DELETE FROM downloads WHERE user_id = %s"
            await cursor.execute(query, (userId,))
            await conn.commit()

            # Delete from songlikes
            query = "DELETE FROM songlikes WHERE user_id = %s"
            await cursor.execute(query, (userId,))
            await conn.commit()

            # Finally, delete the user
            query = "DELETE FROM injustifyusers WHERE id = %s"
            await cursor.execute(query, (userId,))
            await conn.commit()

            return {"success": True, "message": "User deleted successfully."}

    except Exception as e:
        logging.error(f"Error deleting user: {e}")
        return {"success": False, "message": f"Error deleting user: {str(e)}"}

    finally:
        if conn:
            await Config.pool.release(conn)



async def handle_notifications_settings(userId, notifications):
    print('NOTIFICATION SETTINGS:', notifications)

    conn = await Config.get_db_connection()

    if not userId:
        return {"success": False, "message": "User ID is required."}

    try:
        async with conn.cursor() as cursor:
            fields = []
            values = []

            def append_field(key, column=None):
                if column is None:
                    column = key
                if key in notifications:
                    fields.append(f"{column} = %s")
                    values.append(notifications[key])

            # Flat fields
            append_field('enableSoundAlerts', 'enable_sound_alerts')
            append_field('selectedSound', 'selected_sound')
            append_field('enabledDND', 'do_not_disturb')
            # append_field('dndStartTime', 'dnd_start_time')
            # append_field('dndEndTime', 'dnd_end_time')
            append_field('dnd_start_time', None)
            append_field('dnd_end_time', None)
            append_field('dndAllowCalls', 'dnd_allow_calls')
            append_field('dndAllowMessages', 'dnd_allow_messages')
            append_field('dndAllowUrgent', 'dnd_allow_urgent')

            # Email notifications
            for key in ['newSignIn', 'newFeatures', 'newGifts', 'weeklyReport']:
                append_field(key, f'email_{key.lower()}')

            # Device notifications
            for key in ['allNotifications', 'newLikes', 'newComments', 'onlyNewNoty']:
                append_field(key, f'device_{key.lower()}')

            if not fields:
                return {"success": False, "message": "No notification fields provided to update."}

            columns = ["user_id"] + [field.split(" = ")[0] for field in fields]
            placeholders = ["%s"] * len(columns)
            insert_values = [userId] + values
            update_values = values  # Reuse for ON DUPLICATE KEY

            set_clause = ', '.join(fields)

            query = f"""
                INSERT INTO notification_settings ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE {set_clause}
            """

            await cursor.execute(query, insert_values + update_values)
            await conn.commit()

            return {"success": True, "message": "Notification settings updated successfully 💫."}

    except Exception as e:
        logging.error(f"Error updating notification settings: {e}")
        return {"success": False, "message": f"Error updating notification settings: {str(e)}"}

    finally:
        if conn:
            await Config.pool.release(conn)



import logging
from datetime import datetime, timedelta
from config import Config

logging.basicConfig(level=logging.INFO)

async def check_token_existency(email):
    try:
        conn = await Config.get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT expires_at FROM verification_sessions WHERE email = %s",
                (email,)
            )
            result = await cursor.fetchone()

            if result:
                expires_at = result[0]

                if datetime.utcnow() > expires_at:
                    await cursor.execute(
                        "DELETE FROM verification_sessions WHERE email = %s",
                        (email,)
                    )
                    await conn.commit()
                    return False  # Expired token was removed

                return True  # Token exists and is valid

        return False  # No token found

    except Exception as e:
        logging.error(f"Error checking token: {e}")
        return False 
    
    finally:
        if conn:
            await Config.pool.release(conn)  

async def set_token(email, token):
    try:
        if await check_token_existency(email):
            return {"success": False, "message": "A valid token already exists for the given email."}

        expires_at = datetime.utcnow() + timedelta(minutes=30)
        conn = await Config.get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO verification_sessions (email, token, expires_at) VALUES (%s, %s, %s)",
                (email, token, expires_at)
            )
            await conn.commit()

        return {"success": True, "message": "Token sent successfully!"}

    except Exception as e:
        logging.error(f"Error setting token: {e}")
        return {"success": False, "message": "An error occurred while setting the token."}

async def validate_token(email, token, delete=False):
    if not email or not token:
        return {"valid": False, "message": "Email and token are required.","requestNewToken": False}

    try:
        conn = await Config.get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT token, expires_at FROM verification_sessions WHERE email = %s",
                (email,)
            )
            result = await cursor.fetchone()

            if not result:
                return {"valid": False, "message": "No token found for the given email or the token is invalid.","requestNewToken": False }

            setToken, expires_at = result

            if datetime.utcnow() > expires_at:
                await cursor.execute("DELETE FROM verification_sessions WHERE email = %s", (email,))
                await conn.commit()
                return {"valid": False, "message": "Token expired. Kindly request for new token codes!.", "requestNewToken": True}
        


            if token == setToken:
                query = "UPDATE injustifyusers SET verified_email = TRUE WHERE email = %s"
                await cursor.execute(query, (email,))
                await conn.commit()
                
                if delete:
                    await cursor.execute("DELETE FROM verification_sessions WHERE email = %s", (email,))
                    await conn.commit()
                
                return {"valid": True, "message": "Verification successful!", "requestNewToken": False}
            
    

        return {"valid": False, "message": "Verification failed. Token mismatch.","requestNewToken": True}
    
    except Exception as e:
        logging.error(f"Error during token validation: {e}")
        return {"valid": False, "message": "An error occurred during validation. Please try again later."}

    finally:
        if conn:
            await Config.pool.release(conn)  

async def extract_tracking_info(dev_info: dict, device: str):
    tracking_info = {
        "ip": dev_info.get("ip", "Unknown IP"),
        "continent": dev_info.get("continent", "Unknown Continent"),
        "country": dev_info.get("country", "Unknown Country"),
        "region": dev_info.get("region", "Unknown Region"),
        "city": dev_info.get("city", "Unknown City"),
        "latitude": dev_info.get("latitude", 0.0),
        "longitude": dev_info.get("longitude", 0.0),
        "timezone": dev_info.get("timezone", {}).get("id", "Unknown Timezone"),
        "local_time": dev_info.get("timezone", {}).get("current_time", datetime.utcnow().isoformat()),
        "isp_org": dev_info.get("connection", {}).get("org", "Unknown Org"),
        "isp_name": dev_info.get("connection", {}).get("isp", "Unknown ISP"),
        "flag_emoji": dev_info.get("flag", {}).get("emoji", "🏳️"),
        "device": device
    }

    conn = await Config.get_db_connection()

    if not conn:
        print("Database connection failed")
        return

    query = """
        INSERT INTO visitor_tracking (
            ip, continent, country, region, city, latitude, longitude,
            timezone, local_time, isp_org, isp_name, flag_emoji, device
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        tracking_info["ip"],
        tracking_info["continent"],
        tracking_info["country"],
        tracking_info["region"],
        tracking_info["city"],
        tracking_info["latitude"],
        tracking_info["longitude"],
        tracking_info["timezone"],
        tracking_info["local_time"],
        tracking_info["isp_org"],
        tracking_info["isp_name"],
        tracking_info["flag_emoji"],
        tracking_info["device"]
    )

    try:
        async with conn.cursor() as cursor:
            await cursor.execute(query, values)
            await conn.commit()
    except Exception as e:
        print(f"Failed to insert tracking info: {e}")
    finally:
        if conn:
            await Config.pool.release(conn)  
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import random
import socketio
from config import Config
import asyncio
from utils.globalDb import update_view_count,likeUnlike
from utils.sp_handler import Search_suggestions_spotify
from utils.userDb import delete_song_from_downloads, handle_notifications_settings
import json

app = FastAPI()

class INJUserNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace=None):
        super().__init__(namespace or "/inj-user")
    
    async def on_connect(self, sid, environ):
        logging.info(f"✅ User connected: {sid}")
    
    async def on_disconnect(self, sid):
        logging.info(f"❌ User disconnected: {sid}")
    
    async def on_fetchNoty(self, sid, data):
        song_id = data.get("songId", 0)
        noty_type = data.get("type", "")
        
        if not song_id:
            await self.emit("thisNoty", [], room=sid)
            return
        
        your_notifications = []  # Placeholder
        await self.emit("thisNoty", {"your_notifications": your_notifications, "Notytype": noty_type}, room=sid)
    
    async def on_loginUser(self, sid, data):
        username = data.get("userLoggedEmail", "")
        logging.info(f"🔓 User {username} logged in.")
        await self.emit("message", {"msg": f"Hello {username}, welcome!", "type": "success"}, room=sid)
    
    async def on_message(self, sid, msg):
        logging.info(f"📩 Message received: {msg}")
        await self.emit("message", {"msg": msg,'type':'info'}, room=sid)
    
    async def on_updateViewCount(self, sid, data):
        if not isinstance(data, dict):
            logging.error("❌ Invalid data type received. Expected a dictionary.")
            return
        
        song_id = data.get("songId")
        user_id = data.get("userId")
        song_percentage = data.get("progress")
        
        if not song_id or not user_id or song_percentage is None:
            logging.error(f"⚠️ Missing required data: songId={song_id}, userId={user_id}, progress={song_percentage}")
            return
        
        await update_view_count(song_id, user_id, song_percentage)

    async def on_likeUnlikeSong(self, sid,data):
        userId = data.get('userId')
        songId = data.get('songId')
        
        if not userId or not songId:
            await self.emit('message', {
                'type': 'error',
                'message': 'Error: Missing required data for liking & unliking song'
            })
            return

        result = await likeUnlike(songId, userId)
        
        if result['success']:
            await self.emit('message', {
                'type': 'success',
                'message': result.get('message'),
                'likes': result.get('newUPdate')
            }, room=sid)
        else:
            logging.error("Error updating song and view")
            await self.emit('message', {
                'type': 'error',
                'message': result.get('message')
            })
    
    async def on_request_image(self, sid):
        images = {
            "1": f"{Config.BACKEND_SERVER}/static/animation_files/1d6cff39a8b9a75245a06b970be123dd.gif",
            "2": f"{Config.BACKEND_SERVER}/static/animation_files/giphy (3).gif",
            "3": f"{Config.BACKEND_SERVER}/static/animation_files/5y4jl6.gif",         
            "4": f"{Config.BACKEND_SERVER}/static/animation_files/infinite-the-jackal-rubiks-cube.gif",
            "5": f"{Config.BACKEND_SERVER}/static/animation_files/background-waterfall.gif",
            "6": f"{Config.BACKEND_SERVER}/static/animation_files/wp2757861.webp",
            "7": f"{Config.BACKEND_SERVER}/static/animation_files/b20e20379e0def016644ab0b4cc1ebda.gif",
            "8": f"{Config.BACKEND_SERVER}/static/animation_files/tumblr_mn394hFgMI1rasznao1_500.gif",
            "9": f"{Config.BACKEND_SERVER}/static/animation_files/tenor (1).gif",
            "10": f"{Config.BACKEND_SERVER}/static/animation_files/tenor (2).gif",
            "11": f"{Config.BACKEND_SERVER}/static/animation_files/tenor (3).gif",
            "12": f"{Config.BACKEND_SERVER}/static/animation_files/pixel-jeff-galaxy-far-far-away.gif",
            "13": f"{Config.BACKEND_SERVER}/static/animation_files/jackal-running.gif",
            "14": f"{Config.BACKEND_SERVER}/static/animation_files/infinite-the-jackal-fnf-vs-infinite.gif",
            "15": f"{Config.BACKEND_SERVER}/static/animation_files/infinite-loop-anime-girl.gif",
            "16": f"{Config.BACKEND_SERVER}/static/animation_files/icegif-944.gif",
            "17": f"{Config.BACKEND_SERVER}/static/animation_files/Gif-Animated-Wallpaper-Background-Full-HD-Free-Download-for-PC-Macbook-261121-Wallpaperxyz.com-19.webp",
            "18": f"{Config.BACKEND_SERVER}/static/animation_files/demon-slayer.gif",
            "19": f"{Config.BACKEND_SERVER}/static/animation_files/demon-slayer-kimetsu-no-yaiba.gif",
            "20": f"{Config.BACKEND_SERVER}/static/animation_files/dark-mode image.jpg",
            "21": f"{Config.BACKEND_SERVER}/static/animation_files/anime-gif-thunder.gif",
            "22": f"{Config.BACKEND_SERVER}/static/animation_files/16110235550769308128.gif",
            "23": f"{Config.BACKEND_SERVER}/static/animation_files/1479838616hx01_2.gif",
            "24": f"{Config.BACKEND_SERVER}/static/animation_files/62f2ccde1b2fffb43f05ce2e8219cc35.gif",
            "25": f"{Config.BACKEND_SERVER}/static/animation_files/772a6ea88ccedb26a196ab3ff4d57af2.gif",
            "26": f"{Config.BACKEND_SERVER}/static/animation_files/wp2757868.webp",
            "27": f"{Config.BACKEND_SERVER}/static/animation_files/869910.webp",
            "28": f"{Config.BACKEND_SERVER}/static/animation_files/23-24-59-615_512.webp",
            "29": f"{Config.BACKEND_SERVER}/static/animation_files/23f3cf8ba3737bf0145f8d8baec1e9b1.gif",
            "30": f"{Config.BACKEND_SERVER}/static/animation_files/WMZD_hxsTTVz4NCrnM0tOJP81MSPnwMTLVavevaLNhk.gif",
            "31": f"{Config.BACKEND_SERVER}/static/animation_files/R (1).gif",
            "32": f"{Config.BACKEND_SERVER}/static/animation_files/R.gif",
            "33": f"{Config.BACKEND_SERVER}/static/animation_files/giphy (8).gif",
            "34": f"{Config.BACKEND_SERVER}/static/animation_files/giphy.gif",
            "35": f"{Config.BACKEND_SERVER}/static/animation_files/215948.gif",
        }

        image_url = random.choice(list(images.values()))  
        asyncio.create_task(self.emit("animatesd_player", {"image": image_url}, room=sid))

    

    async def on_get_search_suggestions(self,sid, data):
        try:

            if not isinstance(data, dict):
                await self.emit("message", {'message': f'Invalid data format received: {data}','type':'error'}, room=sid)
                return

            userId = data.get('userId')
            query = data.get('query', '').strip().lower()


            if not query:
                await self.emit("message", {'message': 'No query provided!','type':'error'}, room=sid)
                return

            results = await Search_suggestions_spotify(query)
            #print('FOUND::',results)
            await self.emit("respoce_search_suggestions", {'search_suggestions': results}, room=sid)

        except Exception as e:
            print(f"Error in on_get_search_suggestions: {str(e)}")
            if sid:
                await self.emit("message", {'message': f"An error occurred: {str(e)}",'type':'error'}, room=sid)


    async def on_deleteDownload(self,sid,data):
        try:
            if not isinstance(data, dict):
                await self.emit("message", {'message': f'Invalid data format received: {data}','type':'error'}, room=sid)
                return
            songId = data.get('downloadId')
            userId = data.get('userId')

            if not songId or not userId:
                await self.emit("message", {'message': 'No songId or userId provided!','type':'error'}, room=sid)
                return
            
            delete_download_task = await  delete_song_from_downloads(songId, userId)
            if delete_download_task.get('success'):
               await self.emit("message", {'message':delete_download_task.get('message'),'type':'success' }, room=sid)
            else:
               await self.emit("message", {'message':delete_download_task.get('message'),'type':'error' }, room=sid)

        except Exception as e:
            print(f"Error in on_deleteDownload: {str(e)}")
            if sid:
                await self.emit("message", {'message': f"An error occurred: {str(e)}",'type':'error'}, room=sid)


   

    async def on_updateNotificationSettings(self, sid, data):
        try:
            if not isinstance(data, dict):
                await self.emit("message", {
                    'message': f'Invalid data format received: {data}',
                    'type': 'error'
                }, room=sid)
                return

            userId = data.get('userId')
            enableSoundAlerts = data.get('enableSoundAlerts')
            selectedSound = data.get('selectedSound')
            enabledDND = data.get('enableDND')  # Adjusted to match frontend key
            dndStartTime = data.get('dndStartTime')
            dndEndTime = data.get('dndEndTime')
            dndAllowCalls = data.get('dndAllowCalls')
            dndAllowMessages = data.get('dndAllowMessages')
            dndAllowUrgent = data.get('dndAllowUrgent')

            # Email Notification Categories
            emailNotification = {
                'newSignIn': data.get('newSignIn'),
                'newFeatures': data.get('newFeatures'),
                'newGifts': data.get('newGifts'),
                'weeklyReport': data.get('weeklyReport'),
            }

            # Device Notification Categories
            deviceNotification = {
                'allNotifications': data.get('allNotifications'),
                'newLikes': data.get('newLikes'),
                'newComments': data.get('newComments'),
                'onlyNewNoty': data.get('onlyNewNoty'),
            }

            # Build structured notification settings object
            notifications = {
                'emailNotification': emailNotification,
                'deviceNotification': deviceNotification,
                'enableSoundAlerts': enableSoundAlerts,
                'selectedSound': selectedSound,
                'enabledDND': enabledDND,
                'dndStartTime': dndStartTime,
                'dndEndTime': dndEndTime,
                'dndAllowCalls': dndAllowCalls,
                'dndAllowMessages': dndAllowMessages,
                'dndAllowUrgent': dndAllowUrgent
            }

            result = await handle_notifications_settings(userId, notifications)
            if result.get('success'):
                await self.emit("message", {
                    'message': result.get('message'),
                    'type': 'success'
                }, room=sid)
            else:
                await self.emit("message", {
                    'message': result.get('message'),
                    'type': 'error'
                }, room=sid)

        except Exception as e:
            print(f"Error in on_updateNotificationSettings: {str(e)}")
            if sid:
                await self.emit("message", {
                    'message': f"An error occurred: {str(e)}",
                    'type': 'error'
                }, room=sid)

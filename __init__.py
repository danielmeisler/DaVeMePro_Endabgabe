from cgi import test
from cmath import pi
import math
from nturl2path import url2pathname
from unicodedata import name
import requests
import os
import cv2
import numpy as np
import webbrowser
import bpy
import base64

# information
bl_info = {
    "name": "Spotify API Visualizer",
    "author": "Samuel Kasper, Alexander Reiprich, David Niemann, Daniel Meisler",
    "version": (1.2, 0),
    "blender": (2, 91, 0),
    "category": "Add Mesh",
}

# main
def main():
    # selects all objects
    bpy.ops.object.select_all(action='SELECT')  
    # deletes all object
    bpy.ops.object.delete(use_global=False, confirm=False)
    # deletes all leftover meshdata etc.
    bpy.ops.outliner.orphans_purge()  



CLIENT_ID = "56651af3c4134034b9977c0a650b2cdf"
CLIENT_SECRET = "ba05f9e81dbc4443857aa9f3afcfc88b"
REDIRECT_URL = "http://127.0.0.1:5555/callback.html"

# DO NOT PUSH WHEN USER_CODE AND access_token_user IS NOT ""!!!
global user_code
user_code = ""

global access_token_user
access_token_user = ""

AUTH_URL = "https://accounts.spotify.com/api/token"
CLIENT_AUTH_URL = "https://accounts.spotify.com/authorize"
BASE_URL = "https://api.spotify.com/v1/"

# size of the total cover
COVER_SIZE = 1.2  
# distance between the color components until a new material is created
COVER_POSITION = (-2.6819, 1.10, 3.34549)
PROFILE_POSITION = (0.229749, 1.1, 2.18236)

PIXEL_LEVEL = 0.01
WAIT_TIME = 5.0
ARTIST_CHANGE_TIME = 10.0
CURRENT_ARTIST_POS = 0
TRENDING_CHANGE_TIME = 10.0
ANIM_FRAME_RATE = 24

song_id = ""
# get access token
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})
auth_response_data = auth_response.json()
access_token = auth_response_data['access_token']

headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}

# dict with needed weblinks
links = {"Spotify" : 'https://developer.spotify.com/console/get-users-currently-playing-track/?market=&additional_types=',}

# propertygroup with needed properties for the panel
class MyProperties(bpy.types.PropertyGroup):
    bl_idname = "MyProperties"
        
    spotify_user_token: bpy.props.StringProperty(
        name="Token",
        description="You need to generate a Spotify-Acces-Token and put it here to get acces to the data.",
        default="",
    )
    
    train_speed: bpy.props.FloatProperty(name= "Train Duration", soft_min= 20, soft_max= 50, default= 20)

    refresh_timer: bpy.props.FloatProperty(name= "Timer", soft_min= 1, soft_max= 10, default= 1)
    
# panel for the user input
class SPOTIFY_PT_panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Spotify Addon"
    bl_idname = "SPOTIFY_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Spotify Addon"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        token_url = layout.operator('wm.url_open', text="Get Spotify Token", icon="URL")
        token_url.url = links["Spotify"]

        layout.prop(mytool, "spotify_user_token")
        layout.prop(mytool, "train_speed")
        layout.prop(mytool, "refresh_timer")
        self.layout.operator('button.execute', text='Ausführen')

# operator for the button on the panel
class executeAction(bpy.types.Operator):
    bl_idname = "button.execute"
    bl_label = "execute"

    def execute(self, context):
        global access_token_user
        access_token_user = bpy.data.scenes["Scene"].my_tool.spotify_user_token

        Songcover()
        return {'FINISHED'}

# start of the application
class Songcover():
    def __init__(self):
        # clear()
        Songcover.clear_environment()
        Songcover.create_environment()
        Songcover.getCurrentlyPlayedSong()
        # set current frame
        Songcover.set_sun_to_curr_frame()
        Songcover.animation_handler()
        Songcover.create_board_from_image(Songcover.getLinkToCurUserImage(), "profile", PROFILE_POSITION)
        # getArtistAndNameOfCurSong()
        # getLinkToCurUserImage()
        # getCurPlaybackState()
        # getMsIntoCurSong()
        # getProgressIntoCurSong()
        # getCoverOfCurrentSong()
        # updateCurrentSong()
        bpy.app.timers.register(Songcover.run_every_n_second)
        bpy.app.timers.register(Songcover.update_top_artist)
        bpy.app.timers.register(Songcover.update_trending_track)
        # start animation
        bpy.ops.screen.animation_play()

    def requestAuthorization():
        url = CLIENT_AUTH_URL
        url += "?client_id=" + CLIENT_ID
        url += "&response_type=code"
        url += "&redirect_uri=" + REDIRECT_URL
        url += "&show_dialog=true"
        url += "&scope=user-read-currently-playing user-read-playback-position user-read-playback-state"
        webbrowser.open(url, new=0, autoraise=True)


    # gets the access token from the user code from the function above
    # this code automatically gets stored in "access_token_user" and is needed for anything that has to do with user activity
    def getAccessToken():
        encoded = base64.b64encode(
            (CLIENT_ID + ":" + CLIENT_SECRET).encode("utf-8")).decode("utf-8")
        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        r = requests.post(
            url="https://accounts.spotify.com/api/token",
            data={
                "code": user_code,
                "grant_type": "authorization_code",
                "redirect_uri": "http://127.0.0.1:5555/callback.html"
            },
            headers=headers,
            json=True
        )
        access_token_user = r.json().get("access_token")
        print(access_token_user)

    # gets playback state of current device, if true, something is playing
    def getCurPlaybackState():
        curPlayingUrl = BASE_URL + "me/player"
        header = {
            'Authorization': f'Bearer {access_token_user}'.format(token=access_token)
        }
        r = requests.get(url=curPlayingUrl, headers=header)
        respJson = r.json()

        return respJson["is_playing"]

    # returns the milliseconds that have passed since the song began
    def getMsIntoCurSong(): 
        curPlayingUrl = BASE_URL + "me/player"
        header = {
            'Authorization': f'Bearer {access_token_user}'.format(token=access_token)
        }
        r = requests.get(url=curPlayingUrl, headers=header)
        respJson = r.json()
        return respJson["progress_ms"]


    # returns the percentage of how much the song is over
    def getProgressIntoCurSong(): 

        max_length = Songcover.getCurrentlyPlayedSong()["duration"]
        cur_position = Songcover.getMsIntoCurSong()
        return((cur_position / max_length) * 100)


    # returns an object containing information about the currently played song
    def getCurrentlyPlayedSong():
        global access_token_user
        curPlayingUrl = BASE_URL + "me/player/currently-playing"
        header = {
            'Authorization': f'Bearer {access_token_user}'.format(token=access_token)
        }
        r = requests.get(url=curPlayingUrl, headers=header)
        respJson = r.json()

        track_id = respJson["item"]["id"]
        track_name = respJson["item"]["name"]
        artists = respJson["item"]["artists"]
        artists_names = ", ".join([artist["name"] for artist in artists])
        duration = respJson["item"]["duration_ms"]
        link = respJson["item"]["external_urls"]["spotify"]

        currentTrackInfo = {
            "id": track_id,
            "name": track_name,
            "artists": artists_names,
            "duration": duration,
            "link": link
        }
        return currentTrackInfo

    # gets artist and name of current song in this format:
    # "artist, artist2 - song"
    def getArtistAndNameOfCurSong(): 
        currentTrackInfo = Songcover.getCurrentlyPlayedSong()
        return currentTrackInfo["artists"] + " - " + currentTrackInfo["name"]

    # gets the artist image of the current song
    def getArtistImage(track_id):
        track_req = requests.get(BASE_URL + "tracks/" + track_id, headers=headers)
        track_data = track_req.json()
        artist_id  = track_data["artists"][0]["id"]

        artist_req = requests.get(BASE_URL + "artists/" + artist_id, headers=headers)
        artist_data = artist_req.json()
        image = requests.get(artist_data["images"][0])
        img_string = np.frombuffer(image.content, np.uint8)
        img = cv2.imdecode(img_string, cv2.IMREAD_UNCHANGED)
        return img

    # gets the users profile image
    def getLinkToCurUserImage():
        userUrl = BASE_URL + "me"
        header = {
            'Authorization': f'Bearer {access_token_user}'.format(token=access_token)
        }
        r = requests.get(url=userUrl, headers=header)
        if (r.status_code == 200):
            respJson = r.json()
            image = requests.get(respJson["images"][0]["url"])
            img_string = np.frombuffer(image.content, np.uint8)
            img = cv2.imdecode(img_string, cv2.IMREAD_UNCHANGED)
            return img
        else:
            image = requests.get("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png")
            img_string = np.frombuffer(image.content, np.uint8)
            img = cv2.imdecode(img_string, cv2.IMREAD_UNCHANGED)
            return img

    # gets current users top 3 artists of this month
    def getCurUserTopArtists():
        topArtistsUrl = BASE_URL + "me/top/artists?time_range=medium_term&limit=3&offset=0"
        header = {
            'Authorization': f'Bearer {access_token_user}'.format(token=access_token)
        }
        r = requests.get(url=topArtistsUrl, headers=header)
        if (r.status_code == 200):
            respJson = r.json()
            if (len(respJson["items"]) < 3):
                topArtists = ["Artists of the Month", "No Data", "Artists of the Month", "No Data"]
                return topArtists
            else:   
                topArtists = ["Artists of the Month", respJson["items"][0]["name"], respJson["items"][1]["name"], respJson["items"][2]["name"]]
                return topArtists
        else:
            topArtists = ["Artists of the Month", "No Data", "Artists of the Month", "No Data"]
            return topArtists
        

    # gets current users top track of this week
    def getCurUserTopSong(): 
        topTrackUrl = BASE_URL + "me/top/tracks?time_range=short_term&limit=1&offset=0"
        header = {
            'Authorization': f'Bearer {access_token_user}'.format(token=access_token)
        }
        r = requests.get(url=topTrackUrl, headers=header)
        if (r.status_code == 200):
            respJson = r.json()
            return ["Currently Trending", respJson["items"][0]["name"]]
        else:
            return ["Currently Trending", "No Data"]


    # get current users display name
    def getCurUserDisplayName():
        displayUrl = BASE_URL + "me"
        header = {
            'Authorization': f'Bearer {access_token_user}'.format(token=access_token)
        }
        r = requests.get(url=displayUrl, headers=header)
        respJson = r.json()
        
        return respJson["display_name"]

    # gets cover of current song
    def getCoverOfCurrentSong():
        currentTrackId = Songcover.getCurrentlyPlayedSong()["id"]
        Songcover.getSongImage(currentTrackId)


    # gets cover from track id
    def getSongImage(track_id):
        global COVER_POSITION
        r = requests.get(BASE_URL + "tracks/" + track_id, headers=headers)
        d = r.json()

        # get image part
        cover_image = requests.get(d["album"]["images"][0]['url'])
        img_string = np.frombuffer(cover_image.content, np.uint8)
        img = cv2.imdecode(img_string, cv2.IMREAD_UNCHANGED)
        Songcover.create_board_from_image(img, "cover", COVER_POSITION)


    # loop that checks if the song has changed
    def updateCurrentSong():
        global song_id 
    
        song_info = Songcover.getCurrentlyPlayedSong()
        if song_info["id"] != song_id:
            song_id = song_info["id"]
            Songcover.clear_console()
            print("--- Now Playing ---")
            print(Songcover.getArtistAndNameOfCurSong())
            return True
        return False
            
    # updates the cover if a new song is playing
    def update_cover(): 
        Songcover.delete_current_cover()
        Songcover.getCoverOfCurrentSong()
        titel = bpy.data.objects["Song Titel"]
        songdata = Songcover.getCurrentlyPlayedSong()
        titel.data.body = songdata["name"]

    # deletes the cover if it is not playing anymore
    def delete_current_cover():
        bpy.ops.object.select_all(action='DESELECT')
        cover = bpy.context.scene.objects.get('cover')
        if cover:
            bpy.data.objects['cover'].select_set(True)
            bpy.ops.object.delete()

    # creates cover from image retrieved in getSongImage()
    def create_board_from_image(img, name, position):
        global COVER_SIZE

        bpy.ops.mesh.primitive_plane_add(
        size=COVER_SIZE, location=position, rotation=(pi/2, 0, pi))

        cover_object: bpy.types.Object = bpy.data.objects["Plane"]

        mat = Songcover.create_board_material(img)
        cover_object.data.materials.append(mat)
        cover_object.name = name

    # creates material for the cover
    def create_board_material(cover_img):
        global COVER_SIZE
        global PIXEL_LEVEL
        mat: bpy.types.Material = bpy.data.materials.new("mat_Cover")
        mat.use_nodes = True
        node_tree: bpy.types.NodeTree = mat.node_tree

        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs[20].default_value = 4
        tex_image = node_tree.nodes.new('ShaderNodeTexImage')

        rgba = cv2.cvtColor(cover_img, cv2.COLOR_RGB2BGRA)
        rows, cols, _ = cover_img.shape
        reversed_y = rgba[::-1]
        l = reversed_y.reshape(-2)
        list_pixel = l.tolist()
        pxl = [i/255 for i in list_pixel]
        img = bpy.data.images.new(
            "cover image", width=rows, height=cols)
        img.pixels.foreach_set(pxl)
        tex_image.image = img

        node_tree.links.new(
            bsdf.inputs['Base Color'], tex_image.outputs['Color'])
        vector_math = node_tree.nodes.new('ShaderNodeVectorMath')
        node_tree.links.new(
            tex_image.inputs['Vector'], vector_math.outputs['Vector'])
        vector_math.operation = 'SNAP'

        vector_math.inputs[1].default_value[0] = PIXEL_LEVEL
        vector_math.inputs[1].default_value[1] = PIXEL_LEVEL
        vector_math.inputs[1].default_value[2] = PIXEL_LEVEL

        tex_coordinates = node_tree.nodes.new('ShaderNodeTexCoord')
        node_tree.links.new(
            vector_math.inputs['Vector'], tex_coordinates.outputs['Generated'])
        node_tree.links.new(
            bsdf.inputs['Emission'], tex_image.outputs['Color'])
        return mat

    # creates the song title on the tram
    def create_song_titel():
        mat = bpy.data.materials.get("Window_Light")
        songdata = Songcover.getCurrentlyPlayedSong()
        Titel_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
        Titel_curve.body = songdata["name"]
        titel_obj = bpy.data.objects.new(
            name="Song Titel", object_data=Titel_curve)
        bpy.context.scene.collection.objects.link(titel_obj)
        bpy.context.view_layer.objects.active = bpy.data.objects["Song Titel"]
        bpy.context.view_layer.objects.active.data.materials.append(mat)
        titel_obj.rotation_euler = (pi/2, 0, pi)
        titel_obj.scale = (0.4, 0.4, 0.4)
        tram = bpy.data.objects["Strassenbahn"]
        titel_obj.parent = tram
        titel_obj.location = (+4, +0.35, -0.78)
        titel_obj.color = (0, 0, 0, 0)

    # creates the spotify user name on the left panel
    def create_display_name():
        mat = bpy.data.materials.get("Window_Light")
        displayname = Songcover.getCurUserDisplayName()
        displayname_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
        displayname_curve.body = displayname
        titel_obj = bpy.data.objects.new(
            name="Displayname", object_data=displayname_curve)
        bpy.context.scene.collection.objects.link(titel_obj)
        bpy.context.view_layer.objects.active = bpy.data.objects["Displayname"]
        bpy.context.view_layer.objects.active.data.materials.append(mat)
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY")
        titel_obj.rotation_euler = (pi/2, -(pi/2), pi)
        titel_obj.scale = (0.26, 1.45, 1)
        left_panel = bpy.data.objects["Halterung_4"]
        titel_obj.parent = left_panel
        titel_obj.location = (-0.34, -0.85, -0.9)
        titel_obj.color = (0, 0, 0, 0)

    # creates the top artists on the right panel
    def create_top_artists():
        mat = bpy.data.materials.get("Window_Light")
        artists = Songcover.getCurUserTopArtists()
        artists_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
        artists_curve.body = artists[0]
        artists_obj = bpy.data.objects.new(
            name="Top-Artists", object_data=artists_curve)
        bpy.context.scene.collection.objects.link(artists_obj)
        bpy.context.view_layer.objects.active = bpy.data.objects["Top-Artists"]
        bpy.context.view_layer.objects.active.data.materials.append(mat)
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY")
        artists_obj.rotation_euler = (pi/2, 0, pi)
        artists_obj.scale = (0.32, 0.61, 0.65)
        left_panel = bpy.data.objects["Halterung_5"]
        artists_obj.parent = left_panel
        artists_obj.location = (1.32, -0.88, -0.2)
        artists_obj.color = (0, 0, 0, 0)

    # creates the top tracks on the blimp panel
    def create_top_track(): 
        mat = bpy.data.materials.get("Window_Light")
        track = Songcover.getCurUserTopSong()[1]
        track_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
        track_curve.body = track
        track_obj = bpy.data.objects.new(
            name="Top-Track", object_data=track_curve)
        bpy.context.scene.collection.objects.link(track_obj)
        bpy.context.view_layer.objects.active = bpy.data.objects["Top-Track"]
        bpy.context.view_layer.objects.active.data.materials.append(mat)
        track_obj.rotation_euler = (pi/2, (pi/2), pi)
        track_obj.scale = (0.22, 1.34, 1)
        right_panel = bpy.data.objects["Halterung_3"]
        track_obj.parent = right_panel
        track_obj.location = (0.38, -0.75, 0.94)
        track_obj.color = (0, 0, 0, 0)

    # clears the environment to start on an empty space
    def clear_environment(): 
        # Select all objects
        bpy.ops.object.select_all(action='SELECT')
        # Delete the selected Objects
        bpy.ops.object.delete(use_global=False, confirm=False)
        # Delete mesh-data
        bpy.ops.outliner.orphans_purge()
        # Delete materials
        for material in bpy.data.materials:
            bpy.data.materials.remove(material, do_unlink=True)

    # clears console
    def clear_console():
        os.system('cls')
    
    # takes the user input on how fast should be everything refreshed
    def run_every_n_second():
        global WAIT_TIME
        WAIT_TIME = bpy.data.scenes["Scene"].my_tool.refresh_timer
        global counter
        global TEST_SONG_COVERS
    
        is_new_song = Songcover.updateCurrentSong()
        if is_new_song: 
            Songcover.update_cover()
            Songcover.animation_handler()
            
        #update sun position
        Songcover.set_sun_to_curr_frame()
        #counter += 1
        return WAIT_TIME   

    # refreshes the blimp panel with the top artists from the current user
    def update_top_artist():
        global CURRENT_ARTIST_POS
        allArtists = Songcover.getCurUserTopArtists()
        curArtist = allArtists[CURRENT_ARTIST_POS]
        artists = bpy.data.objects["Top-Artists"]
        artists.data.body = curArtist
        if CURRENT_ARTIST_POS == 3:
            CURRENT_ARTIST_POS = 0
        else:
            CURRENT_ARTIST_POS = CURRENT_ARTIST_POS + 1

        return ARTIST_CHANGE_TIME

    # refreshes the left panel with the top track that is currently trending
    def update_trending_track():
        global TRENDING_CHANGE_TIME
        track = bpy.data.objects["Top-Track"]
        if track.data.body == "Currently Trending":
            track.data.body = Songcover.getCurUserTopSong()[1]
        else:
            track.data.body = "Currently Trending"

        return TRENDING_CHANGE_TIME
        


    # import assets for the environment
    def create_environment():
        file_path = 'DAVT_Project_Scene.blend'
        inner_path = 'Object'
        object_names = {'Building 1','Building 2','Building 3','Building 4','Building 5','Building 5_2','Building 6','Building 7','Building 8',
                        'Bridge', 'City_Floor', 'Nature_Floor','Street_Light', 'Street_Light_2','Zaun','Roof_Lamp', 'Camera', 
                        'DepthOfField_Point', 'sun', 'Halterung', 'Halterung_2', 'Halterung_3', 'Halterung_4', 'Halterung_5', 'Straba_Light_Inside', 
                        'Street_Light_Top', 'Point.001', 'Street_Light_Top2','Point.002', 'Blimp_Wing4'}
       
        for obj in object_names:
            bpy.ops.wm.append(
                filepath=os.path.join(file_path, inner_path, obj),
                directory=os.path.join(file_path, inner_path),
                filename=obj)

        Songcover.create_song_titel()
        Songcover.create_display_name()
        Songcover.create_top_artists()
        Songcover.create_top_track()

    # sets all animations
    def animation_handler():

        # delete old keyframes / animation
        for a in bpy.data.actions:
            bpy.data.actions.remove(a)

        # get duration of playing song
        songdata = Songcover.getCurrentlyPlayedSong()
        seconds = songdata["duration"]/1000
        last_frame = math.floor(seconds)*ANIM_FRAME_RATE

        # set keyframes
        Songcover.sun_animation(last_frame)
        Songcover.world_background_animation(last_frame)
        Songcover.train_animation(last_frame)

    # sun animation
    def sun_animation(last_frame):
        # variables
        sun_start_x = 27
        sun_z = 14.5
        sun_end_x = -27
        sun_start_rot = 0.959931
        sun_end_rot = -0.959931
        sun_start_color = (sun_start_x, 0, sun_z) 
        start_end_color = (sun_end_x, 0, sun_z)

        # get sun obj
        sun: bpy.types.Object = bpy.data.objects["sun"]
        sun_spot: bpy.data.lights = bpy.data.lights["Spot"]

        # set animation length
        bpy.data.scenes["Scene"].frame_end = last_frame

        # set keyframes for location and rotation of the sun
        # set first keyframe
        sun.location = sun_start_color
        sun.rotation_euler[1] = sun_start_rot
        sun_spot.color = (0.743, 0.785, 1)
        sun.keyframe_insert(data_path="location", frame=0)
        sun.keyframe_insert(data_path="rotation_euler", frame=0)
        sun_spot.keyframe_insert(data_path="color", frame=0)

        # set last keyframe 
        sun.location = start_end_color
        sun.rotation_euler[1] = sun_end_rot
        sun_spot.color = (1, 0.746, 0.722)
        sun.keyframe_insert(data_path="location", frame=last_frame)
        sun.keyframe_insert(data_path="rotation_euler", frame=last_frame)
        sun_spot.keyframe_insert(data_path="color", frame=last_frame)

    # heaven animation
    def world_background_animation(last_frame):
        world_bg_dark = (0.013,0.016,0.024,1)
        world_bg_bright = (0.085, 0.097,0.138, 1)

        world_background = bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0]

        world_background.default_value = world_bg_dark
        world_background.keyframe_insert(data_path="default_value", frame=0)
        world_background.keyframe_insert(data_path="default_value", frame=last_frame)

        world_background.default_value = world_bg_bright
        world_background.keyframe_insert(data_path="default_value", frame=math.floor(last_frame/2))

    # train animation
    def train_animation(last_frame):
        train_start_x = 8
        train_end_x = -10
        start_frame = math.floor(last_frame/10)
        train_speed = math.floor(bpy.data.scenes["Scene"].my_tool.train_speed) #min. 20 - max. 50 
        if train_speed < 20:
            train_speed = 20
        
        train_duration = ANIM_FRAME_RATE * train_speed

        # get train obj
        train: bpy.types.Object = bpy.data.objects["Strassenbahn"]

        train.location[0] = train_start_x
        train.keyframe_insert(data_path="location", frame=start_frame)

        train.location[0] = train_end_x
        train.keyframe_insert(data_path="location", frame=start_frame+train_duration)

    # the sun will be set to the current frame
    def set_sun_to_curr_frame():
        bpy.data.scenes["Scene"].frame_current = math.floor((Songcover.getMsIntoCurSong()/1000)*ANIM_FRAME_RATE)

# autostart
class Autostart(bpy.types.Operator):
    bl_idname = "spotify.api"
    bl_label = "Spotify API Visualizer"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main()
        return {'FINISHED'}

# all registered classes and properties
def register():
    bpy.utils.register_class(Autostart)
    bpy.utils.register_class(MyProperties)
    bpy.utils.register_class(SPOTIFY_PT_panel)
    bpy.utils.register_class(executeAction)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type= MyProperties)

# all unregistered classes and properties
def unregister():
    bpy.utils.unregister_class(Autostart)
    bpy.utils.unregister_class(MyProperties)
    bpy.utils.unregister_class(SPOTIFY_PT_panel)
    bpy.utils.unregister_class(executeAction)
    del bpy.types.Scene.my_tool

# name
if __name__ == "__main__":
    register()

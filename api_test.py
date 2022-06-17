
from cmath import pi
import math
import requests
import os
import cv2
import numpy as np
import webbrowser
import bpy
import base64

CLIENT_ID = "56651af3c4134034b9977c0a650b2cdf"
CLIENT_SECRET = "ba05f9e81dbc4443857aa9f3afcfc88b"
REDIRECT_URL = "http://127.0.0.1:5555/callback.html"

# DO NOT PUSH WHEN USER_CODE AND access_token_user IS NOT ""!!!
user_code = ""
access_token_user = "BQCKt5EK-kprD6frisQFMCxot-KOptPtGVJ9KyG9AUJUGDIIgxrf002-PCGlfe8twveTtSLAm_yW6TeXs0kDnvpAePjk2-Ph3wBZjiMDpvd-aHe0AQ8NrkqstVZNKvpgf0D0D6KMPNcW_XwZ9UoJMX_d1bUtJr7mbHSamgMdMiiWDP0RfYeuz9Z_gYaP2OaSpcxWm_nxn7kIcUhmnQ"

AUTH_URL = "https://accounts.spotify.com/api/token"
CLIENT_AUTH_URL = "https://accounts.spotify.com/authorize"
BASE_URL = "https://api.spotify.com/v1/"

COVER_SIZE = 1.2  # size of the total cover
# distance between the color components until a new material is created
COVER_POSITION = (-2.6819, 1.10, 3.34549)

PIXEL_LEVEL = 0.01
WAIT_TIME = 5.0


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

# Opens login screen -> After redirect, you can see the code. (Live Server must be active!)
# This code goes into "USER_CODE"


def requestAuthorization():
    url = CLIENT_AUTH_URL
    url += "?client_id=" + CLIENT_ID
    url += "&response_type=code"
    url += "&redirect_uri=" + REDIRECT_URL
    url += "&show_dialog=true"
    url += "&scope=user-read-currently-playing user-read-playback-position user-read-playback-state"
    webbrowser.open(url, new=0, autoraise=True)


# Gets the access token from the user code from the function above
# This code automatically gets stored in "access_token_user" and is needed for anything that has to do with user activity

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

# Gets playback state of current device, if true, something is playing


def getCurPlaybackState():
    curPlayingUrl = BASE_URL + "me/player"
    header = {
        'Authorization': f'Bearer {access_token_user}'.format(token=access_token)
    }
    r = requests.get(url=curPlayingUrl, headers=header)
    respJson = r.json()

    return respJson["is_playing"]

# Returns the milliseconds that have passed since the song began


def getMsIntoCurSong():
    curPlayingUrl = BASE_URL + "me/player"
    header = {
        'Authorization': f'Bearer {access_token_user}'.format(token=access_token)
    }
    r = requests.get(url=curPlayingUrl, headers=header)
    respJson = r.json()
    return respJson["progress_ms"]


# Returns the percentage of how much the song is over

def getProgressIntoCurSong():

    max_length = getCurrentlyPlayedSong()["duration"]
    cur_position = getMsIntoCurSong()
    return((cur_position / max_length) * 100)


# Returns an object containing information about the currently played song

def getCurrentlyPlayedSong():
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

# Gets artist and name of current song in this format:
# "artist, artist2 - song"


def getArtistAndNameOfCurSong():
    currentTrackInfo = getCurrentlyPlayedSong()
    return currentTrackInfo["artists"] + " - " + currentTrackInfo["name"]

# Gets the artist image of the current song


def getArtistImage(track_id):
    track_req = requests.get(BASE_URL + "tracks/" + track_id, headers=headers)
    track_data = track_req.json()
    artist_id = track_data["artists"][0]["id"]

    artist_req = requests.get(
        BASE_URL + "artists/" + artist_id, headers=headers)
    artist_data = artist_req.json()
    image = requests.get(artist_data["images"][0])
    img_string = np.frombuffer(image.content, np.uint8)
    img = cv2.imdecode(img_string, cv2.IMREAD_UNCHANGED)
    return img

# Gets the users profile image


def getLinkToCurUserImage():
    userUrl = BASE_URL + "me"
    header = {
        'Authorization': f'Bearer {access_token_user}'.format(token=access_token)
    }
    r = requests.get(url=userUrl, headers=header)
    respJson = r.json()
    image = requests.get(respJson["images"][0]["url"])
    img_string = np.frombuffer(image.content, np.uint8)
    img = cv2.imdecode(img_string, cv2.IMREAD_UNCHANGED)
    return img


# Gets cover of current song

def getCoverOfCurrentSong():
    currentTrackId = getCurrentlyPlayedSong()["id"]
    getSongImage(currentTrackId)


# Gets cover from track id

def getSongImage(track_id):
    r = requests.get(BASE_URL + "tracks/" + track_id, headers=headers)
    d = r.json()

    # Get image part
    cover_image = requests.get(d["album"]["images"][0]['url'])
    img_string = np.frombuffer(cover_image.content, np.uint8)
    img = cv2.imdecode(img_string, cv2.IMREAD_UNCHANGED)
    create_cover_from_image(img)

    # Show pixeled cover image
    """resized = cv2.resize(img, (100, 100), interpolation=cv2.INTER_NEAREST)
    cv2.namedWindow('img', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('img', 500, 500)
    cv2.imshow('img', resized)
    cv2.waitKey(0)"""


# Loop that checks if the song has changed

def updateCurrentSong():
    global song_id

    song_info = getCurrentlyPlayedSong()
    if song_info["id"] != song_id:
        song_id = song_info["id"]
        clear_console()
        print("--- Now Playing ---")
        getArtistAndNameOfCurSong()
        return True
    return False


def update_cover():
    delete_current_cover()
    getCoverOfCurrentSong()
    titel = bpy.data.objects["Song Titel"]
    songdata = getCurrentlyPlayedSong()
    titel.data.body = songdata["name"]
    


def delete_current_cover():
    bpy.ops.object.select_all(action='DESELECT')
    cover = bpy.context.scene.objects.get('cover')
    if cover:
        bpy.data.objects['cover'].select_set(True)
        bpy.ops.object.delete()
# Creates cover from image retrieved in getSongImage()


def generate_collection():
    collection = bpy.data.collections.new("Leuchtbilder")
    bpy.context.scene.collection.children["Leuchtbildtafel"].children.link(
        collection)


def create_song_titel():
    songdata = getCurrentlyPlayedSong()
    """ layer_collection = bpy.context.view_layer.layer_collection.children[
        "Straßenbahn"]
    bpy.context.view_layer.active_layer_collection = layer_collection """
    Titel_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
    Titel_curve.body = songdata["name"]
    titel_obj = bpy.data.objects.new(
        name="Song Titel", object_data=Titel_curve)
    bpy.context.scene.collection.children["Straßenbahn"].objects.link(
        titel_obj)
    titel_obj.rotation_euler = (pi/2, 0, pi)
    titel_obj.scale = (0.4, 0.4, 0.4)
    tram = bpy.data.objects["Straßenbahn"]
    titel_obj.parent = tram
    titel_obj.location = (+4, +0.35, -0.78)
    titel_obj.color = (0, 0, 0, 0)


def create_cover_from_image(img):
    global COVER_SIZE
    global COVER_POSITION

    layer_collection = bpy.context.view_layer.layer_collection.children[
        "Leuchtbildtafel"].children["Leuchtbilder"]
    bpy.context.view_layer.active_layer_collection = layer_collection

    bpy.ops.mesh.primitive_plane_add(
        size=COVER_SIZE, location=COVER_POSITION, rotation=(pi/2, 0, pi))

    cover_object: bpy.types.Object = bpy.data.objects["Plane"]

    mat = create_cover_material(img)
    cover_object.data.materials.append(mat)
    cover_object.name = "cover"


def create_cover_material(cover_img):
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
    vcector_math = node_tree.nodes.new('ShaderNodeVectorMath')
    node_tree.links.new(
        tex_image.inputs['Vector'], vcector_math.outputs['Vector'])
    vcector_math.operation = 'SNAP'

    vcector_math.inputs[1].default_value[0] = PIXEL_LEVEL
    vcector_math.inputs[1].default_value[1] = PIXEL_LEVEL
    vcector_math.inputs[1].default_value[2] = PIXEL_LEVEL

    tex_coordinates = node_tree.nodes.new('ShaderNodeTexCoord')
    node_tree.links.new(
        vcector_math.inputs['Vector'], tex_coordinates.outputs['Generated'])
    node_tree.links.new(
        bsdf.inputs['Emission'], tex_image.outputs['Color'])
    return mat

# Clears console


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


def clear_console():
    os.system('cls')


def run_every_n_second():
    global WAIT_TIME
    global counter
    global TEST_SONG_COVERS

    is_new_song = updateCurrentSong()
    if is_new_song:
        update_cover()
        animation_handler()

    # update sun position
    set_sun_to_curr_frame()

    #counter += 1
    return WAIT_TIME

# import assets for the environment


def create_environment():
    bpy.ops.wm.open_mainfile(filepath="DAVT_Project_Scene.blend")
    create_song_titel()


def animation_handler():

    # delete old keyframes / animation
    for a in bpy.data.actions:
        bpy.data.actions.remove(a)

    # set/get frame rate
    frame_rate = 30

    # get duration of playing song
    songdata = getCurrentlyPlayedSong()
    seconds = songdata["duration"]/1000
    last_frame = math.floor(seconds*frame_rate)

    # set keyframes
    sun_animation(last_frame)
    world_background_animation(last_frame)
    train_animation(last_frame, frame_rate)

    # set current frame
    set_sun_to_curr_frame()

    # start animation
    # bpy.ops.screen.animation_play()


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


def world_background_animation(last_frame):
    world_bg_dark = (0.013, 0.016, 0.024, 1)
    world_bg_bright = (0.085, 0.097, 0.138, 1)

    world_background = bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0]

    world_background.default_value = world_bg_dark
    world_background.keyframe_insert(data_path="default_value", frame=0)
    world_background.keyframe_insert(
        data_path="default_value", frame=last_frame)

    world_background.default_value = world_bg_bright
    world_background.keyframe_insert(
        data_path="default_value", frame=math.floor(last_frame/2))


def train_animation(last_frame, frame_rate):
    train_start_x = 8
    train_end_x = -10
    start_frame = math.floor(last_frame/4)
    train_speed = 50  # 20
    train_duration = frame_rate * train_speed
    #end_frame = math.floor(last_frame/2 + last_frame/10)

    # get train obj
    train: bpy.types.Object = bpy.data.objects["Straßenbahn"]

    train.location[0] = train_start_x
    train.keyframe_insert(data_path="location", frame=start_frame)

    train.location[0] = train_end_x
    train.keyframe_insert(data_path="location",
                          frame=start_frame+train_duration)


def set_sun_to_curr_frame():
    bpy.data.scenes["Scene"].frame_current = math.floor(
        (getMsIntoCurSong()/1000)*30)


if (__name__ == "__main__"):
    # clear()
    clear_environment()
    create_environment()
    generate_collection()
    animation_handler()
    # requestAuthorization()
    # getAccessToken()
    # getSong("3I2Jrz7wTJTVZ9fZ6V3rQx")
    # getArtistsAlbums("26T3LtbuGT1Fu9m0eRq5X3")
    # getSongImage("3I2Jrz7wTJTVZ9fZ6V3rQx")
    # getArtistAndNameOfCurSong()
    # getArtistImage("50lTDu2BnjyqWnUFsxMryJ")
    # getLinkToCurUserImage()
    # getCurPlaybackState()
    # getMsIntoCurSong()
    # getProgressIntoCurSong()
    # getCoverOfCurrentSong()
    getCurrentlyPlayedSong()
    # updateCurrentSong()
    bpy.app.timers.register(run_every_n_second)

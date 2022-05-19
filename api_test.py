from cmath import pi
import time
import bmesh
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
access_token_user = ""

AUTH_URL = "https://accounts.spotify.com/api/token"
CLIENT_AUTH_URL = "https://accounts.spotify.com/authorize"
BASE_URL = "https://api.spotify.com/v1/"

COVER_SIZE = 10  # size of the total cover
# distance between the color components until a new material is created
COLOR_DIFFERECE = 0.2
COVER_POSITION_X = 6
COVER_POSITION_Y = 0
COVER_POSITION_Z = 38

plane_amount = 200  # Length of the square covers
materials = []  # saves all materials
material_index = []  # Indices which materials should be assigned to the faces

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
    link = respJson["item"]["external_urls"]["spotify"]

    currentTrackInfo = {
        "id": track_id,
        "name": track_name,
        "artists": artists_names,
        "link": link
    }
    return currentTrackInfo

# Gets cover of current song


def getCoverOfCurrentSong():
    currentTrackId = getCurrentlyPlayedSong()["id"]
    getSongImage(currentTrackId)


# Gets song from track id

def getSong(track_id):
    r = requests.get(BASE_URL + "tracks/" + track_id, headers=headers)
    d = r.json()

    artist = d["artists"][0]["name"]
    track = d["name"]
    print(artist, "-", track)
    print()


# Gets cover from track id

def getSongImage(track_id):
    getSong(track_id)
    r = requests.get(BASE_URL + "tracks/" + track_id, headers=headers)
    d = r.json()

    # Get image part
    cover_image = requests.get(d["album"]["images"][0]['url'])
    img_string = np.frombuffer(cover_image.content, np.uint8)
    img = cv2.imdecode(img_string, cv2.IMREAD_COLOR)
    createCoverFromImage(img)

    # Show pixeled cover image
    """resized = cv2.resize(img, (100, 100), interpolation=cv2.INTER_NEAREST)
    cv2.namedWindow('img', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('img', 500, 500)
    cv2.imshow('img', resized)
    cv2.waitKey(0)"""


# Gets all albums from artist | test function, could be removed?

def getArtistsAlbums(artist_id):

    r = requests.get(BASE_URL + "artists/" + artist_id,
                     headers=headers)
    a = r.json()

    print("--- All Albums by the Artist '" + a["name"] + "' ---")

    r = requests.get(BASE_URL + "artists/" + artist_id + "/albums",
                     headers=headers,
                     params={"include_groups": "album", "limit": 50})
    d = r.json()

    albums = []
    for album in d["items"]:
        album_name = album["name"]

        trim_name = album_name.split('(')[0].strip()  # Filter out duplicates
        if trim_name.upper() in albums:
            continue

        albums.append(trim_name.upper())

        print(album_name, "---", album["release_date"])

    print()


# Loop that checks if the song has changed

def updateCurrentSong():
    song_id = ""
    while True:
        song_info = getCurrentlyPlayedSong()
        if song_info["id"] != song_id:
            song_id = song_info["id"]
            clear()
            print("--- Now Playing ---")
            getSong(song_id)
        time.sleep(1)


# Creates cover from image retrieved in getSongImage()

def createCoverFromImage(img):
    global COVER_SIZE
    global COVER_POSITION_X
    global COVER_POSITION_Y
    global COVER_POSITION_Z
    global plane_amount
    global materials
    global material_index
    # If plane amount is bigger than image size, set plane amount to image size
    rows, cols, _ = img.shape
    if(rows < plane_amount):
        if(cols < plane_amount):
            plane_amount = cols
        else:
            plane_amount = rows

    verts = []

    cover_mesh = bpy.data.meshes.new("cover mesh")
    cover_object = bpy.data.objects.new("cover", cover_mesh)
    bpy.context.collection.objects.link(cover_object)
    bm = bmesh.new()
    bm.from_mesh(cover_mesh)
    #cover_object.parent = bpy.data.objects["skyscraper"]

    # Create Material
    for i in range(plane_amount):
        for j in range(plane_amount):
            createMaterial(img[int(i*rows/plane_amount),
                           int(j*cols/plane_amount)])
    # adds all materials to the object
    for i in range(len(materials)):
        cover_object.data.materials.append(materials[i])
    #  Creating the verts
    for x in range(plane_amount + 1):
        verts.append([])
        for y in range(plane_amount + 1):
            new_vert = bm.verts.new(
                (COVER_POSITION_X, ((y - plane_amount/2)/(plane_amount / COVER_SIZE)) + COVER_POSITION_Y, (-(x-plane_amount/2)/(plane_amount / COVER_SIZE))+COVER_POSITION_Z))
            verts[x].append(new_vert)
    # Connect 4 verts to a face and append to faces array
    bm.verts.ensure_lookup_table()
    face_counter = 0
    for x in range(len(verts)-1):
        for y in range(len(verts[x])-1):
            new_face = bm.faces.new(
                (verts[x][y], verts[x][y+1], verts[x+1][y+1], verts[x+1][y]))
            new_face.material_index = material_index[face_counter]
            face_counter += 1

    bm.to_mesh(cover_mesh)
    bm.free()
    """ bpy.data.objects["cover"].location[0] = COVER_POSITION_X
    bpy.data.objects["cover"].location[0] = COVER_POSITION_Y
    bpy.data.objects["cover"].location[2] = COVER_POSITION_Z """


# creates a new material or matches material index with the appropriate material for the faces

def createMaterial(color):
    global materials
    global material_index

    new_color = (round(color[2]/255, 1),
                 round(color[1]/255, 1),
                 round(color[0]/255, 1),
                 1)
    # check if a similar color already exists and if so, return its index
    index = material_is_already_available(new_color)
    # if color exists already append it. Otherwise create a new material.
    if(index == -1):
        new_mat = bpy.data.materials.new(
            'mat_' + str(len(materials)))
        new_mat.diffuse_color = new_color
        material_index.append(len(materials))
        materials.append(new_mat)
    else:
        material_index.append(index)


# checks if there is already a material for a specific color. If so, returns its index. Otherwise returns -1.

def material_is_already_available(color):
    global materials
    global COLOR_DIFFERECE
    for i in range(len(materials)):
        if (materials[i].diffuse_color[0] + COLOR_DIFFERECE > color[0] and materials[i].diffuse_color[0] - COLOR_DIFFERECE < color[0]):
            if (materials[i].diffuse_color[1] + COLOR_DIFFERECE > color[1] and materials[i].diffuse_color[1] - COLOR_DIFFERECE < color[1]):
                if(materials[i].diffuse_color[2] + COLOR_DIFFERECE > color[2] and materials[i].diffuse_color[2] - COLOR_DIFFERECE < color[2]):
                    return i
    return -1

# Clears console


def clear():
    os.system('cls')
    # Select all objects
    bpy.ops.object.select_all(action='SELECT')
    # Delete the selected Objects
    bpy.ops.object.delete(use_global=False, confirm=False)
    # Delete mesh-data
    bpy.ops.outliner.orphans_purge()
    # Delete materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material, do_unlink=True)

# import assets for the environment


def createEnvironment():
    bpy.ops.wm.open_mainfile(filepath="skyscraper.blend")
    skyscraper_degree = 90
    skyscraper_scale = 6
    bpy.data.objects["skyscraper"].rotation_euler[2] = skyscraper_degree * pi / 180
    bpy.data.objects["skyscraper"].location[2] *= skyscraper_scale
    for i in range(3):
        bpy.data.objects["skyscraper"].scale[i] = skyscraper_scale


if (__name__ == "__main__"):
    clear()
    createEnvironment()
    # requestAuthorization()
    # getAccessToken()
    # getSong("3I2Jrz7wTJTVZ9fZ6V3rQx")
    # getArtistsAlbums("26T3LtbuGT1Fu9m0eRq5X3")
    getSongImage("3I2Jrz7wTJTVZ9fZ6V3rQx")
    # getCoverOfCurrentSong()
    # getCurrentlyPlayedSong()
    # updateCurrentSong()

import requests
import os
import matplotlib.pyplot as plt
import cv2

CLIENT_ID = "56651af3c4134034b9977c0a650b2cdf"
CLIENT_SECRET = "ba05f9e81dbc4443857aa9f3afcfc88b"

AUTH_URL = "https://accounts.spotify.com/api/token"
BASE_URL = "https://api.spotify.com/v1/"

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

def getSong(track_id):
    r = requests.get(BASE_URL + "tracks/" + track_id, headers=headers)
    d = r.json()

    artist = d["artists"][0]["name"]
    track = d["name"]
    print("--- Chosen Track ---")
    print(artist, "-", track)
    print()

def getArtistsAlbums(artist_id):

    r = requests.get(BASE_URL + "artists/" + artist_id,
                    headers=headers)
    a = r.json()

    # Get image part
    cover_image = requests.get(a["images"][0]['url'])
    with open("coverImage.png", 'wb') as f:
        f.write(cover_image.content) 
    
    #Get Pixalized
    img = cv2.imread('coverImage.png')
    resized = cv2.resize(img, (25,25), interpolation=cv2.INTER_LINEAR)
    resized = cv2.resize(img, (50,50), interpolation=cv2.INTER_NEAREST)
    cv2.namedWindow('img', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('img', 500, 500)
    cv2.imshow('img', resized)
    cv2.waitKey(0)
       
    # Get image part end

    print("--- All Albums by the Artist '" + a["name"] + "' ---")

    r = requests.get(BASE_URL + "artists/" + artist_id + "/albums",
                    headers=headers,
                    params={"include_groups": "album", "limit": 50})
    d = r.json()
    
    albums = []
    for album in d["items"]:
        album_name = album["name"]

        trim_name = album_name.split('(')[0].strip() # Filter out duplicates
        if trim_name.upper() in albums:
            continue
            
        albums.append(trim_name.upper())

        print(album_name, "---", album["release_date"])
    
    print()

def clear(): 
    os.system('cls')

if (__name__ == "__main__"):
    clear()
    getSong("3I2Jrz7wTJTVZ9fZ6V3rQx")
    getArtistsAlbums("26T3LtbuGT1Fu9m0eRq5X3")

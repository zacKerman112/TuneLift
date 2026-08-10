import os
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, session
from flask_cors import CORS
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
SCOPE = "user-library-read playlist-read-private playlist-modify-public playlist-modify-private"


def create_spotify_oauth():
    """Вспомогательная функция для инициализации SpotifyOAuth."""
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope=SCOPE,
        show_dialog=True,
    )
    


@app.route("api/auth/spotify/login")
def login():
    """ссылка для входа"""
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return jsonify({'auth_url': auth_url})    


@app.route("/callback")
def callback():
    """Callback-эндпоинт, куда Spotify возвращает пользователя с кодом"""
    sp_oauth = create_spotify_oauth
    session.clear()
    
    code = request.args.get("code")
    error = request.args.get("error")
    
    if error:
        return jsonify({"error": error}), 400
    
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect("http://localhost:5173/auth-success")


def get_token():
    """Вспомогательная функция для получения актуального токена (с авто-обновлением)"""
    token_info = session.get('token_info', None)
    if not token_info:
        return None
    sp_oauth = create_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(
            token_info["refresh_token"]
        )
        session["token_info"] = token_info
    return token_info    


@app.route("/api/spotify/playlists")
def get_user_playlists():
    """Пример защищенного эндпоинта: Получить список плейлистов пользователя"""
    token_info = get_token()
    if not token_info:
        return jsonify({"error": "User not authenticated"}), 401
    sp = spotipy.Spotify(auth=token_info["access_token"])
    playlists = sp.current_user_playlists()
    result = []
    for item in playlists["items"]:
        result.append(
            {
                "id": item["id"],
                "name": item["name"],
                "tracks_count": item["tracks"]["total"],
                "image": (
                    item["images"][0]["url"] if item["images"] else None
                ),
            }
        )

    return jsonify({"playlists": result})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
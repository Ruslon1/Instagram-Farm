import os
import time
import typer
from instagrapi import Client
import getpass
import moviepy
import json
import random

app = typer.Typer()

captions = []
with open("captions.json", "r") as outfile:
    captions = json.load(outfile)

def upload_photos(username: str, password: str, folder_path: str):
    try:
        cl = Client()

        cl.login(username, password)

        files = os.listdir(folder_path)

        files.sort()

        upload_interval = 600

        for file_name in files:
            file_path = os.path.join(folder_path, file_name)
            print(file_name)
            if file_name.endswith(('.mp4')):
                print("updaupda")
                media = cl.video_upload(
                    path=file_path,
                    caption=random.choice(captions) + "\n#vlogging#beach#layingdown#whereatcomefrom#green#sand#red#ishowspeed#red#sunny#gettingtothebag#55154#subscribers#daily#wegotthis#sofunny#fish"
                    )
                typer.echo(f"Uploaded: {file_name}")
            
            time.sleep(random.randint(300, 2000))

    except Exception as e:
        typer.echo(f"Error: {e}")

@app.command()
def main():
    #username = typer.prompt("Enter your Instagram username:")
    #password = typer.prompt("Enter your Instagram password:")
    #folder_path = typer.prompt("Enter the folder path containing files to upload:")
    
    upload_photos("ishowclipspeed", "vfFInQnoOP", "./video")

if __name__ == "__main__":
    app()

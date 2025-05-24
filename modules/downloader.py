import subprocess

def download_tiktok_video(url, output_file):
    try:
        command = [
            "python",
            "tiktok_no_water_mark.py",
            "-url", url,
            "-o", output_file
        ]
        subprocess.run(command, check=True)
        print(f"Видео успешно сохранено в {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при загрузке видео: {e}")

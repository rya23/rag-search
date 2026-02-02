import os
import requests

url = "https://kvongcmehsanalibrary.wordpress.com/wp-content/uploads/2021/07/harrypotter.pdf"
folder = "data"
filename = "harrypotter.pdf"
filepath = os.path.join(folder, filename)


def download_pdf(url, folder, filename):
    filepath = os.path.join(folder, filename)
    # Ensure the data folder exists
    os.makedirs(folder, exist_ok=True)

    if os.path.exists(filepath):
        print("File already exists:", filepath)
    else:
        print("File not found. Downloading...")

        response = requests.get(url, stream=True)
        response.raise_for_status()  # fail fast if download breaks

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print("Download complete:", filepath)


if __name__ == "__main__":
    download_pdf(url, folder, filename)

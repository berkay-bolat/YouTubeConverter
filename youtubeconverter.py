import tempfile
import customtkinter as ctk
import subprocess
import threading
import json
import os
import shutil
import requests
from PIL import Image
from io import BytesIO

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ProConverterApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        script_dir = os.path.dirname(__file__)
        icon_path = os.path.join(script_dir, "icon.ico")

        if os.path.exists(icon_path):

            try:

                self.iconbitmap(icon_path)

            except ctk.tkinter.TclError as e:

                print(f"WARNING: Couldn't set window icon. Ensure the icon file is a valid .ico format. Error: {e}")

        else:

            print(f"WARNING: Icon file not found at {icon_path}. Application will run without a custom icon.")

        self.title("YouTube Converter (Beta v1.0)")
        self.geometry("800x540")
        self.video_info = {}
        self.save_path = os.path.join(os.path.expanduser("~"), "Documents", "YouTube Converter")

        if not os.path.exists(self.save_path):

            os.makedirs(self.save_path)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.url_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Paste Your YouTube URL Here", justify="center")
        self.url_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.analyze_button = ctk.CTkButton(self.top_frame, text="Analyze The URL", command=self.start_analysis_thread)
        self.analyze_button.grid(row=0, column=1, padx=10, pady=10)

        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=1, column=0, padx=20, pady=0, sticky="ew")
        self.info_frame.grid_columnconfigure(1, weight=1)
        self.thumbnail_label = ctk.CTkLabel(self.info_frame, text="", width=160, height=90)
        self.thumbnail_label.grid(row=0, column=0, rowspan=3, padx=10, pady=10)
        self.title_label = ctk.CTkLabel(self.info_frame, text="The Video Title Will Be Shown Here", anchor="w", wraplength=650)
        self.title_label.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="ew")
        self.duration_label = ctk.CTkLabel(self.info_frame, text="The Video Duration Will Be Shown Here", text_color="gray", anchor="w", wraplength=650)
        self.duration_label.grid(row=1, column=1, padx=10, pady=(10, 0), sticky="ew")
        self.path_button = ctk.CTkButton(self.info_frame, text="Change Output Path", command=self.select_save_path)
        self.path_button.grid(row=2, column=2, padx=10, pady=5, sticky="e")
        self.path_label = ctk.CTkLabel(self.info_frame, text=f"Output Path: {self.save_path}", text_color="gray", anchor="w")
        self.path_label.grid(row=2, column=1, padx=10, sticky="ew")

        placeholder_path = os.path.join(os.path.dirname(__file__), "placeholder.png")

        if os.path.exists(placeholder_path):

            placeholder_img = Image.open(placeholder_path).resize((160, 90), Image.LANCZOS)

            self.placeholder_ctk_img = ctk.CTkImage(light_image=placeholder_img, dark_image=placeholder_img, size=(160, 90))
        else:

            self.placeholder_ctk_img = None

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1, uniform="equal_frames")
        self.main_frame.grid_columnconfigure(1, weight=1, uniform="equal_frames")
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.video_download_frame = ctk.CTkFrame(self.main_frame)
        self.video_download_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.video_download_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.video_download_frame, text="Video Converter", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=10)

        self.video_formats_menu = ctk.CTkOptionMenu(self.video_download_frame, values=["Video Download Options"], state="disabled")
        self.video_formats_menu.grid(row=1, column=0, padx=10, pady=20, sticky="ew")
        self.download_video_button = ctk.CTkButton(self.video_download_frame, text="Download Video", state="disabled", command=lambda: self.start_download_thread('video', 'mp4'))
        self.download_video_button.grid(row=2, column=0, padx=10, pady=20)

        self.audio_download_frame = ctk.CTkFrame(self.main_frame)
        self.audio_download_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.audio_download_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.audio_download_frame, text="Audio Converter", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=10)

        self.audio_formats = {

            "WAV": "wav",
            "FLAC": "flac",
            "MP3": "mp3",
            "M4A (AAC)": "m4a",
            "OPUS": "opus",
            "OGG (Vorbis)": "ogg"
        }

        self.audio_format_menu = ctk.CTkOptionMenu(self.audio_download_frame, values=["Audio Download Options"], state="disabled")
        self.audio_format_menu.set("Audio Download Options")
        self.audio_format_menu.grid(row=1, column=0, padx=10, pady=20, sticky="ew")
        self.download_audio_button = ctk.CTkButton(self.audio_download_frame, text="Download Audio", state="disabled", command=lambda: self.start_download_thread("audio", self.audio_formats[self.audio_format_menu.get()]))
        self.download_audio_button.grid(row=2, column=0, padx=10, pady=20)

        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(self.bottom_frame, text="Paste your YouTube URL and press the \"Analyze The URL\" button.", justify="center")
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar = ctk.CTkProgressBar(self.bottom_frame)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.format_map = {}
        self.check_dependencies()
        self.set_ui_state("initial")

    def set_ui_state(self, state):

        if state == "initial":

            self.url_entry.configure(state="normal")
            self.analyze_button.configure(state="normal")
            self.path_button.configure(state="normal")
            self.video_formats_menu.configure(state="disabled", values=["Waiting for \"Analyze The File\" button..."])
            self.download_video_button.configure(state="disabled")
            self.audio_format_menu.configure(state="disabled", values=["Audio Download Options"])
            self.audio_format_menu.set("Audio Download Options")
            self.download_audio_button.configure(state="disabled")
            self.title_label.configure(text="The Video Title Will Be Shown Here")
            self.duration_label.configure(text="The Video Duration Will Be Shown Here")

            if self.placeholder_ctk_img:

                self.thumbnail_label.configure(image=self.placeholder_ctk_img)
                self.thumbnail_label.image = self.placeholder_ctk_img

            else:

                self.thumbnail_label.configure(image=None)
                self.thumbnail_label.image = None

            self.progress_bar.set(0)
            self.progress_bar.configure(mode="determinate")
            self.update_status("Paste your YouTube URL and press the \"Analyze The URL\" button.", "white")

        elif state == "analyzing":

            self.url_entry.configure(state="disabled")
            self.analyze_button.configure(state="disabled")
            self.path_button.configure(state="disabled")
            self.video_formats_menu.configure(state="disabled", values=["Analyzing the URL..."])
            self.download_video_button.configure(state="disabled")
            self.audio_format_menu.configure(state="disabled", values=["Audio Download Options"])
            self.audio_format_menu.set("Audio Download Options")
            self.download_audio_button.configure(state="disabled")
            self.title_label.configure(text="Getting URL Data...")
            self.duration_label.configure(text="Getting URL Data...")

            if self.placeholder_ctk_img:

                self.thumbnail_label.configure(image=self.placeholder_ctk_img)
                self.thumbnail_label.image = self.placeholder_ctk_img

            else:

                self.thumbnail_label.configure(image=None)
                self.thumbnail_label.image = None

            self.progress_bar.set(0)
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.update_status("Analyzing the URL...", "yellow")

        elif state == "analysis_complete":

            self.url_entry.configure(state="normal")
            self.analyze_button.configure(state="normal")
            self.path_button.configure(state="normal")
            self.video_formats_menu.configure(state="normal")
            self.download_video_button.configure(state="normal")
            self.audio_format_menu.configure(state="normal", values=list(self.audio_formats.keys()))
            self.audio_format_menu.set(list(self.audio_formats.keys())[0])
            self.download_audio_button.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")

        elif state == "downloading":

            self.url_entry.configure(state="disabled")
            self.analyze_button.configure(state="disabled")
            self.path_button.configure(state="disabled")
            self.video_formats_menu.configure(state="disabled")
            self.download_video_button.configure(state="disabled")
            self.audio_format_menu.configure(state="disabled")
            self.download_audio_button.configure(state="disabled")
            self.progress_bar.set(0)
            self.progress_bar.configure(mode="determinate")
            self.update_status("Downloading...", "yellow")

    def check_dependencies(self):

        yt_dlp_ok = shutil.which("yt-dlp")
        ffmpeg_ok = shutil.which("ffmpeg")

        if not yt_dlp_ok and not ffmpeg_ok:

            self.update_status("ERROR: Couldn't find \"yt-dlp\" and \"FFmpeg\"! Please configure your PATH settings.", "red")
            self.analyze_button.configure(state="disabled")
            self.url_entry.configure(state="disabled")

        elif not yt_dlp_ok:

            self.update_status("ERROR: Couldn't find \"yt-dlp\"! Please configure your PATH settings.", "red")
            self.analyze_button.configure(state="disabled")
            self.url_entry.configure(state="disabled")

        elif not ffmpeg_ok:

            self.update_status("ERROR: Couldn't find \"FFmpeg\"! Please configure your PATH settings.", "red")
            self.analyze_button.configure(state="disabled")
            self.url_entry.configure(state="disabled")

        else:

            self.update_status("Paste your YouTube URL and press the \"Analyze The URL\" button.", "white")

    def update_status(self, message, color="white", progress=None):

        self.status_label.configure(text=message, text_color=color)

        if progress is not None:

            self.progress_bar.set(progress)

        self.update_idletasks()

    def select_save_path(self):

        path = ctk.filedialog.askdirectory(initialdir=self.save_path)

        if path:

            self.save_path = path
            self.path_label.configure(text=f"Current Output Path: {self.save_path}")

    def start_analysis_thread(self):

        url = self.url_entry.get().strip()

        self.set_ui_state("analyzing")

        thread = threading.Thread(target=self.analyze_url, args=(url,))
        thread.daemon = True
        thread.start()

    def analyze_url(self, url):

        try:

            command = f'yt-dlp -j --no-playlist "{url}"'
            # SECURITY NOTE: 'shell=True' is used here for simplicity in this educational project.
            # In a production environment, 'shell=False' should be used and arguments should be passed as a list
            # to prevent potential command injection vulnerabilities.
            process_result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8')

            self.video_info = json.loads(process_result.stdout)
            self.after(0, self.update_ui_after_analysis)

        except (subprocess.CalledProcessError, json.JSONDecodeError, Exception) as e:

            self.after(0, lambda: self.set_ui_state("initial"))
            self.after(0, lambda: self.update_status("ERROR: Failed to analyze the URL. Please check if the link is valid.", "red"))
            self.after(0, lambda: self.progress_bar.stop())
            self.after(0, lambda: self.progress_bar.set(0))
            self.after(0, lambda: self.progress_bar.configure(mode="determinate"))


            print(e)

    def format_duration(self, duration):

        try:

            total_seconds = int(float(duration))
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        except (ValueError, TypeError):

            return "Couldn't Find The Video Duration"

    def update_ui_after_analysis(self):

        self.title_label.configure(text=self.video_info.get("title", "Couldn't Find The Video Title"))

        duration = self.video_info.get("duration")
        formatted_duration = self.format_duration(duration)

        self.duration_label.configure(text="Duration : " + formatted_duration)

        thumb_url = self.video_info.get("thumbnail")

        if thumb_url:

            thread = threading.Thread(target=self.load_thumbnail, args=(thumb_url,))
            thread.daemon = True
            thread.start()

        else:

            self.thumbnail_label.configure(image=None)
            self.thumbnail_label.image = None

        best_formats_by_res_fps = {}

        for f in self.video_info.get('formats', []):

            if f.get('vcodec') != 'none' and f.get('fps'):

                if f.get('ext') == 'm3u8' or 'm3u8' in f.get('url', '') or 'hls' in f.get('format_note', '').lower():

                    continue

                if f.get('height', 0) <= 4320 and f.get('fps', 0) <= 120:

                    fps_val = int(f['fps'])
                    display_key = f"{f['resolution']} - {fps_val}FPS - MP4"
                    current_bitrate = f.get('tbr', 0) or f.get('vbr', 0)

                    if display_key not in best_formats_by_res_fps or current_bitrate > best_formats_by_res_fps[display_key][0]:

                        best_formats_by_res_fps[display_key] = (current_bitrate, f)

        video_formats_display = []

        self.format_map = {}

        for display_text, (bitrate, format_obj) in best_formats_by_res_fps.items():

            format_id = format_obj.get("format_id")
            acodec = format_obj.get("acodec", "none")

            if format_id:

                if acodec == "none":

                    format_id += "+bestaudio"

                video_formats_display.append(display_text)
                self.format_map[display_text] = format_id

        if video_formats_display:

            self.video_formats_menu.configure(values=video_formats_display, state="normal")
            self.video_formats_menu.set(video_formats_display[-1])
            self.download_video_button.configure(state="normal")

        else:

            self.video_formats_menu.configure(values=["Couldn't Find Any Suitable Video Format"], state="disabled")
            self.download_video_button.configure(state="disabled")


        self.audio_format_menu.configure(state="normal", values=list(self.audio_formats.keys()))
        self.audio_format_menu.set(list(self.audio_formats.keys())[0])
        self.download_audio_button.configure(state="normal")
        self.set_ui_state("analysis_complete")
        self.update_status("The analyze has completed. You can select a download option.", progress=1)

    def load_thumbnail(self, url):

        try:

            response = requests.get(url)
            response.raise_for_status()
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img = img.resize((160, 90), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(160, 90))
            self.after(0, lambda: self.thumbnail_label.configure(image=ctk_img))
            self.after(0, lambda: setattr(self.thumbnail_label, 'image', ctk_img))

        except Exception as e:

            print("Couldn't find thumbnail.")

            if self.placeholder_ctk_img:

                self.after(0, lambda: self.thumbnail_label.configure(image=self.placeholder_ctk_img))
                self.after(0, lambda: setattr(self.thumbnail_label, 'image', self.placeholder_ctk_img))

            else:

                self.after(0, lambda: self.thumbnail_label.configure(image=None))
                self.after(0, lambda: setattr(self.thumbnail_label, 'image', None))

            print(e)

    def start_download_thread(self, download_type, target_format):

        self.set_ui_state("downloading")
        self.update_status(f"Dönüştürme için hazırlanılıyor...", progress=0)
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        thread = threading.Thread(target=self.download_and_convert, args=(download_type, target_format))
        thread.daemon = True
        thread.start()

    def download_and_convert(self, download_type, target_format):

        url = self.url_entry.get()
        video_title = self.video_info.get('title', 'video').replace('|', '').replace('"', "").replace('/','').replace('\\', '').replace(':', '').replace('*', '').replace('?', '').replace('<', '').replace('>', '')
        safe_title = "".join([c for c in video_title if c.isalnum() or c in (' ', '-', '_', '.', ',')]).rstrip()
        safe_title = ' '.join(safe_title.split()).replace(' ', '_')
        output_path = os.path.join(self.save_path, f"{safe_title}.{target_format}")

        try:

            if download_type == 'audio':

                self.update_status("Converting/Downloading the audio file...", "yellow")

                temp_audio_path = os.path.join(tempfile.gettempdir(), f"{os.urandom(24).hex()}.%(ext)s")
                yt_dlp_command = f'yt-dlp -f bestaudio -o "{temp_audio_path}" --no-playlist "{url}"'
                # SECURITY NOTE: 'shell=True' is used here for simplicity in this educational project.
                # In a production environment, 'shell=False' should be used and arguments should be passed as a list
                # to prevent potential command injection vulnerabilities.
                subprocess.run(yt_dlp_command, shell=True, check=True, capture_output=True, text=True)

                downloaded_temp_file = None
                temp_dir = os.path.dirname(temp_audio_path)
                base_name_prefix = os.path.basename(temp_audio_path).split('.')[0]

                for fname in os.listdir(temp_dir):

                    if fname.startswith(base_name_prefix):

                        downloaded_temp_file = os.path.join(temp_dir, fname)

                        break

                if not downloaded_temp_file or not os.path.exists(downloaded_temp_file):

                    try:

                        raise Exception()

                    except Exception as e:

                        self.after(0, lambda: self.update_status("ERROR: Couldn't download the audio file.", "red"))

                        print(e)

                ffmpeg_cmd_map = {

                    "wav": f'-i "{downloaded_temp_file}" -ar 48000 -acodec pcm_s16le "{output_path}"',
                    "flac": f'-i "{downloaded_temp_file}" -ar 48000 -acodec flac -compression_level 8 "{output_path}"',
                    "mp3": f'-i "{downloaded_temp_file}" -ar 48000 -b:a 320k "{output_path}"',
                    "m4a": f'-i "{downloaded_temp_file}" -ar 48000 -c:a aac -b:a 320k "{output_path}"',
                    "opus": f'-i "{downloaded_temp_file}" -ar 48000 -c:a libopus -b:a 320k "{output_path}"',
                    "ogg": f'-i "{downloaded_temp_file}" -ar 48000 -c:a libvorbis -q:a 10 "{output_path}"',
                }

                ffmpeg_command = f'ffmpeg -y {ffmpeg_cmd_map[target_format]}'
                # SECURITY NOTE: 'shell=True' is used here for simplicity in this educational project.
                # In a production environment, 'shell=False' should be used and arguments should be passed as a list
                # to prevent potential command injection vulnerabilities.
                subprocess.run(ffmpeg_command, shell=True, check=True, capture_output=True)

                if os.path.exists(downloaded_temp_file):

                    try:

                        os.remove(downloaded_temp_file)

                        print(f"Temporary file has deleted: {downloaded_temp_file}")

                    except Exception as clean_e:

                        print(f"WARNING: Couldn't delete the temporary files! You can delete them manually: {clean_e} - {downloaded_temp_file}")

            elif download_type == 'video':

                selected_format_code = self.format_map.get(self.video_formats_menu.get())

                if not selected_format_code:

                    try:

                        raise Exception()

                    except Exception as e:

                        self.after(0, lambda: self.update_status("ERROR: Select a valid option.", "red"))

                        print(e)

                self.update_status("Converting/Downloading the video file...", "yellow")

                yt_dlp_command = (

                    f'yt-dlp -f "{selected_format_code}" '
                    f'--merge-output-format mp4 '
                    f'--postprocessor-args "-c:a aac -b:a 320k" '
                    f'-o "{output_path}" --no-playlist "{url}"'
                )

                # SECURITY NOTE: 'shell=True' is used here for simplicity in this educational project.
                # In a production environment, 'shell=False' should be used and arguments should be passed as a list
                # to prevent potential command injection vulnerabilities.
                subprocess.run(yt_dlp_command, shell=True, check=True, capture_output=True)

            self.after(0, lambda: self.update_status(f"Process is completed. The file is saved as \"{os.path.basename(output_path)}\".", "lightgreen", progress=1))

        except (subprocess.CalledProcessError, Exception) as e:

            self.after(0, lambda: self.update_status("ERROR: An error occurred while attempting to process the file.", "red"))

            print(e)

        finally:

            self.after(0, self.progress_bar.stop)
            self.after(0, lambda: self.progress_bar.configure(mode="determinate"))
            self.after(0, lambda: self.set_ui_state("analysis_complete"))

if __name__ == "__main__":

    app = ProConverterApp()
    app.mainloop()
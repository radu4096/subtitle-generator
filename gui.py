import tkinter
from tkinter import *
import cv2
import PIL.Image, PIL.ImageTk
from time import sleep
import os
from tkinter import filedialog
import engine
import customtkinter
import subprocess
import pygame
from subhelper import export_subtitiles
from videostream import VideoStream

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("dark-blue")

class App:
    """
    Main application window class
    """

    def __init__(self):
        """ 
        Buids the window
        """

        pygame.init()

        # launching a window to get the file
        currdir = os.getcwd()
        tempdir = filedialog.askopenfile(initialdir=currdir, title='Please select a video file')

        self.window = customtkinter.CTk()
        self.window.title("Subtitles generator")
        self.video_file = tempdir.name

        self.left_frame = customtkinter.CTkFrame(self.window, fg_color="transparent")
        self.left_frame.grid(row = 0, column=0)

        # extracting the subtitles
        command = ".\\ffmpeg\\bin\\ffmpeg -i " + self.video_file + " -ab 160k -ac 2 -ar 44100 -vn media\\raw_audio.wav"
        subprocess.call(command, shell = True)
        pygame.mixer.music.load("media\\raw_audio.wav")

        # Play the audio file
        self.subs = engine.generate_subtitles(".\\media\\raw_audio.wav")
        export_subtitiles(self.subs)
        
        # setting up all the objects for video playing
        self.video = VideoStream(self.video_file)

        fps = self.video.vid.get(cv2.CAP_PROP_FPS)
        frame_count = int(self.video.vid.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = frame_count/fps

        self.video_frame = customtkinter.CTkFrame(self.left_frame, fg_color="black")
        self.canvas = Canvas(self.video_frame, width = self.video.width, height = self.video.height, background="black", borderwidth=2)

        self._initialize_subtitles_params()
        
        self.canvas.grid(row = 0, column = 0)
        self.subtitle_controls_frame = customtkinter.CTkFrame(self.window, fg_color="transparent")
        self.video_controls_frame = customtkinter.CTkFrame(self.left_frame, fg_color="transparent")
        
        self._load_images()
        self._configure_video_buttons()
        self._configure_subs_buttons()
        self._configure_position_buttons()

        self.video_frame.grid(row = 0, column = 0)

        self.delay = (int) ((1 / self.video.vid.get(cv2.CAP_PROP_FPS)) * 1000)

        self.update()

        pygame.mixer.music.play()
        self.window.mainloop()

    def _initialize_subtitles_params(self):
        """
        Sets the initial values for the subtitles
        """
        self.cursor = 0

        # initial state
        self.paused = 0
        self.cc_active = 0
        self.bg_active = 0

        self.x_pos_sub = (int) (self.video.width / 2)
        self.y_pos_sub = (int) (self.video.height * 0.9)
        self.color = (0, 0, 0)

    def _configure_subs_buttons(self):
        """
        Creates and configures the buttons for subtitiles
        """
        self.label_color = customtkinter.CTkLabel(self.subtitle_controls_frame, text = "Subtitle color:", fg_color="transparent")
        self.label_size = customtkinter.CTkLabel(self.subtitle_controls_frame, text = "Subtitle size:", fg_color="transparent")

        self.white = customtkinter.CTkButton(self.subtitle_controls_frame, command=self.set_white, text="", fg_color="white", width=50)
        self.yellow = customtkinter.CTkButton(self.subtitle_controls_frame, command=self.set_yellow, text="", fg_color="yellow", width=50)
        self.black = customtkinter.CTkButton(self.subtitle_controls_frame, command=self.set_black, text="", fg_color="black", width=50)

        self.size_scale = customtkinter.CTkSlider(self.subtitle_controls_frame, from_=0, to=100, orientation="vertical", height=100)
        self.size_scale.set(50)

        self.button_frame.grid(row = 0, column = 0, padx=2, pady=2)
        self.label_color.grid(row = 1, column = 0, padx=2, pady=2)
        self.white.grid(row = 2, column = 0, padx=2, pady=2)
        self.yellow.grid(row = 3, column = 0, padx=2, pady=2)
        self.black.grid(row = 4, column = 0, padx=2, pady=2)

        self.joystick = customtkinter.CTkFrame(self.subtitle_controls_frame, fg_color="transparent")
        self.joystick.grid(row = 5, column = 0, padx=2, pady=2)

        self.label_size.grid(row = 6, column = 0, padx=2, pady=2)
        self.size_scale.grid(row = 7, column = 0, padx=2, pady=2)

        self.subtitle_controls_frame.grid(row = 0, column = 1)
        self.video_controls_frame.grid(row = 1, column=0)
        self.video_controls_frame.configure(width=640)


    def _configure_position_buttons(self):
        """
        Creates and configures the buttons for subtitle position
        """
        self.up = customtkinter.CTkButton(self.joystick, text = "", command=self.move_up, image=self.up_image, fg_color="transparent", width=40)
        self.down = customtkinter.CTkButton(self.joystick, text = "", command=self.move_down, image=self.down_image, fg_color="transparent", width=40)
        self.left = customtkinter.CTkButton(self.joystick, text = "", command=self.move_left, image=self.left_image, fg_color="transparent", width=40)
        self.right = customtkinter.CTkButton(self.joystick, text = "", command=self.move_right, image=self.right_image, fg_color="transparent", width=40)

        self.up.grid(row = 0, column = 1)
        self.left.grid(row = 1, column = 0)
        self.right.grid(row = 1, column = 2)
        self.down.grid(row = 2, column = 1)

        # these are for video control
        self.play_button.grid(row = 0, column = 0, padx=2, pady=2)
        self.progress_bar.grid(row = 0, column = 1, padx=2, pady=2)

    def _configure_video_buttons(self):
        """
        Creates and configures the buttons for video playing
        """
        self.play_button = customtkinter.CTkButton(self.video_controls_frame, text="",
                                  command=self.playpause, image = self.pause_image,
                                  fg_color="transparent", width=50)

        self.progress_bar = customtkinter.CTkProgressBar(self.video_controls_frame, orientation='horizontal',
                                         mode='determinate', )
        
        self.button_frame = customtkinter.CTkFrame(self.subtitle_controls_frame, fg_color="transparent")
        
        self.cc_button = customtkinter.CTkButton(self.button_frame, text = "CC", text_color="black",
                                 command=self.toggle_cc, border_width=2, border_color="black",
                                 fg_color="transparent", width=50)
        
        
        self.bg_button = customtkinter.CTkButton(self.button_frame, text = "BG", text_color="black",
                                 command=self.toggle_bg, border_width=2, border_color="black",
                                 fg_color="transparent", width=50)
        
        self.cc_button.grid(row = 0, column = 0, padx=2, pady=2)
        self.bg_button.grid(row = 0, column = 1, padx=2, pady=2)

    def _load_images(self):
        """
        Loads the images used for button display
        """
        self.play_image = PhotoImage(file = "./resources/play.png").subsample(12, 12)
        self.pause_image = PhotoImage(file = "./resources/pause.png").subsample(12, 12)
        self.cc_image = PhotoImage(file = "./resources/cc.png").subsample(12, 12)
        self.up_image = PhotoImage(file = "./resources/up.png").subsample(14, 14)
        self.down_image = PhotoImage(file = "./resources/down.png").subsample(14, 14)
        self.left_image = PhotoImage(file = "./resources/left.png").subsample(14, 14)
        self.right_image = PhotoImage(file = "./resources/right.png").subsample(14, 14)
    
    def update(self):
        """
        Updates the video frame
        """
        if self.paused == 0:
            ret, frame = self.video.get_frame()

            font = cv2.FONT_HERSHEY_COMPLEX

            if ret:
                time = self.video.vid.get(cv2.CAP_PROP_POS_MSEC) / 1000
                
                if ((time / 1000) / self.duration) * 1000 > 0.99:
                    self.window.destroy()
                
                self.progress_bar.set(((time / 1000) / self.duration) * 1000)
                string = ""

                if self.cursor < len(self.subs):
                    if time < self.subs[self.cursor][0][0]:
                        # I have not reached the window
                        string = ""
                    if time > self.subs[self.cursor][0][0] and time < self.subs[self.cursor][0][1]:
                        # I am in the widow
                        string = self.subs[self.cursor][1]
                    if time > self.subs[self.cursor][0][1]:
                        string = ""
                        self.cursor = self.cursor + 1

                if self.cc_active == 1 and string != "":
                    final_size = 2 * (self.size_scale.get() / 100)
                    whole_text_size = cv2.getTextSize(string, font, final_size, 2)[0][0]

                    if whole_text_size < self.video.width:

                        x_offset = (int) (cv2.getTextSize(string, font, final_size, 2)[0][0] / 2)

                        x = self.x_pos_sub - x_offset
                        y = self.y_pos_sub

                        if self.bg_active:
                            overlay = frame.copy()
                            w = (int) (cv2.getTextSize(string, font, final_size, 2)[0][0])
                            h = (int) ( - cv2.getTextSize(string, font, final_size, 2)[0][1] * 1.5)
                            y = y -  (int) (h / 5)
                            cv2.rectangle(overlay, (x, y), (x+w, y+h), (200, 200, 200), -1)  
  
                            alpha = 0.4 

                            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

                        cv2.putText(frame, string, (x, y), font, final_size, self.color, 2, cv2.LINE_4)
                    else:
                        # there are 2 rows
                        # divide the string
                        x = string.split()
                        string1 = x[0]
                        i = 1
                        while i < len(x):
                            string1 = string1 + " " + x[i]
                            i = i + 1
                            if cv2.getTextSize(string1, font, final_size, 2)[0][0] > (whole_text_size / 2):
                                break
                        string2 = x[i]
                        i = i + 1

                        while i < len(x):
                            string2 = string2 + " " + x[i]
                            i = i + 1
                        
                        # for the first string
                        x_offset1 = (int) (cv2.getTextSize(string1, font, final_size, 2)[0][0] / 2)

                        x1 = self.x_pos_sub - x_offset1
                        y11 = self.y_pos_sub

                        if self.bg_active:
                            overlay = frame.copy()
                            w1 = (int) (cv2.getTextSize(string1, font, final_size, 2)[0][0])
                            h1 = (int) ( - cv2.getTextSize(string1, font, final_size, 2)[0][1] * 1.5)
                            y12 = y11 -  (int) (h1 / 5)
                            cv2.rectangle(overlay, (x1, y12), (x1+w1, y12+h1), (200, 200, 200), -1)  
  
                            alpha = 0.4 

                            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

                        cv2.putText(frame, string1, (x1, y11), font, final_size, self.color, 2, cv2.LINE_4)

                        # for the second string
                        x_offset2 = (int) (cv2.getTextSize(string2, font, final_size, 2)[0][0] / 2)

                        x2 = self.x_pos_sub - x_offset2
                        y21 = self.y_pos_sub - (int) ( - cv2.getTextSize(string1, font, final_size, 2)[0][1] * 1.5)

                        if self.bg_active:
                            overlay = frame.copy()
                            w2 = (int) (cv2.getTextSize(string2, font, final_size, 2)[0][0])
                            h2 = (int) ( - cv2.getTextSize(string2, font, final_size, 2)[0][1] * 1.5)
                            y22 = y21 -  (int) (h2 / 5) + 5
                            cv2.rectangle(overlay, (x2, y22), (x2+w2, y22+h2), (200, 200, 200), -1)  
  
                            alpha = 0.4 

                            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

                        cv2.putText(frame, string2, (x2, y21), font, final_size, self.color, 2, cv2.LINE_4)
                        

                self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
                self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
        self.window.after(self.delay, self.update)
    
    def playpause(self):
        if self.paused == 0:
            self.paused = 1
            self.play_button.configure(image = self.play_image)
            pygame.mixer.music.pause()
        else:
            self.paused = 0
            self.play_button.configure(image = self.pause_image)
            pygame.mixer.music.unpause()

    def toggle_cc(self):
        if self.cc_active == 0:
            self.cc_active = 1
        else:
            self.cc_active = 0
    
    def toggle_bg(self):
        if self.bg_active == 0:
            self.bg_active = 1
        else:
            self.bg_active = 0
    
    def move_up(self):
        self.y_pos_sub = self.y_pos_sub - 10

    def move_down(self):
        self.y_pos_sub = self.y_pos_sub + 10

    def move_right(self):
        self.x_pos_sub = self.x_pos_sub + 10
    
    def move_left(self):
        self.x_pos_sub = self.x_pos_sub - 10
    
    def set_white(self):
        self.color = (255, 255, 255)
    
    def set_yellow(self):
        self.color = (255, 255, 0)

    def set_black(self):
        self.color = (0, 0, 0)


if __name__ == '__main__':
    App()
# AI-based Aquatic Ultrasonic Imaging & Chemical Water Testing
#
# UNIHIKER
#
# By Kutluhan Aktar
#
# Identify noxious air bubbles lurking in the substrate w/ ultrasonic scans
# and assess water pollution based on chemical tests simultaneously.
# 
#
# For more information:
# https://www.hackster.io/kutluhan-aktar


import cv2
import numpy
from edge_impulse_linux.image import ImageImpulseRunner
from unihiker import GUI
from pinpong.board import *
from pinpong.extension.unihiker import *
import os
import requests
import datetime
from time import sleep


class aquarium_func():
    def __init__(self, model_file):
        # Initialize the USB high-quality camera feed.
        self.camera = cv2.VideoCapture(0)
        sleep(2)
        # Define the required variables to establish the connection with the web application — Aquatic_Ultrasonic_Imaging.
        self.web_app = "http://192.168.1.22/Aquatic_Ultrasonic_Imaging/"
        # Define the required variables to configure camera settings.
        self.frame_size_m = (320,320)
        self.frame_size_s = (120,120)
        # Define the required configurations to run the Edge Impulse RetinaNet (NVIDIA TAO) object detection model.
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.model_file = os.path.join(dir_path, model_file)
        self.class_names = ["sterile", "dangerous", "polluted"]
        self.class_colors = ["green", "yellow", "red"]
        self.bb_colors = {"sterile": (0,255,0), "dangerous": (0,255,255), "polluted": (0,0,255)}
        self.selected_class = -1
        self.detected_class = "Pending"
        # Define the required variables to generate an ultrasonic (radar) image.
        self.u_im = {"w": 20, "h": 20, "offset": 20, "temp_path": "./assets/ultrasonic_temp.jpg"}
        # Define the required parameters to transfer information to the given Telegram bot — @aquatic_ultrasonic_bot.
        telegram_bot_token = "<____________>" # e.g., 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
        self.telegram_webhook = "https://api.telegram.org/bot{}".format(telegram_bot_token)
        self.latest_air_label = "..."
        # Initiate the user interface (GUI) on UNIHIKER.
        self.interface = GUI()
        # Initiate the built-in sensor features on UNIHIKER.
        Board().begin()
        # Define the RGB LED pins.
        self.rgb = {"r": Pin(Pin.P4, Pin.OUT), "g": Pin(Pin.P5, Pin.OUT), "b": Pin(Pin.P6, Pin.OUT)}

    def run_inference(self, notify="Telegram", bb_offset=40):
        # Run inference to detect water quality levels based on chemical water tests via object detection.
        with ImageImpulseRunner(self.model_file) as runner:
            try:
                resulting_image = ""
                # Print the information of the Edge Impulse model converted to a Linux (AARCH64) application (.eim).
                model_info = runner.init()
                print('\nLoaded runner for "' + model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
                labels = model_info['model_parameters']['labels']
                # Get the currently captured and modified image via the high-quality USB camera.
                test_img = self.modified_image
                # After obtaining the test frame, resize (if necessary) and generate features from the retrieved frame depending on the provided model so as to run an inference.
                features, cropped = runner.get_features_from_image(test_img)
                res = runner.classify(features)
                # Obtain the prediction (detection) results for each label (class).
                if "bounding_boxes" in res["result"].keys():
                    print('Found %d bounding boxes (%d ms.)' % (len(res["result"]["bounding_boxes"]), res['timing']['dsp'] + res['timing']['classification']))
                    # If the Edge Impulse model predicts a class successfully:
                    if(len(res["result"]["bounding_boxes"]) == 0):
                        self.detected_class = "empty"
                    else:
                        for bb in res["result"]["bounding_boxes"]:
                            # Get the latest detected labels:
                            self.detected_class = bb['label']
                            print('\t%s (%.2f): x=%d y=%d w=%d h=%d' % (bb['label'], bb['value'], bb['x'], bb['y'], bb['width'], bb['height']))
                            cv2.rectangle(cropped, (bb['x']-bb_offset, bb['y']-bb_offset), (bb['x']+bb['width']+bb_offset, bb['y']+bb['height']+bb_offset), self.bb_colors[self.detected_class], 2)
                # Save the generated model resulting image with the passed bounding boxes (if any) to the detections folder.
                if self.detected_class != "empty":
                    date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    resulting_image = "/detections/detection_{}_{}.jpg".format(self.detected_class, date)
                    cv2.imwrite("."+resulting_image, cropped)
                # Notify the user of the model detection results on UNIHIKER.
                self.cam_info_text.config(text="Detection: " + self.detected_class)
                print("\n\nLatest Detected Label => " + self.detected_class)
                if(self.detected_class == "sterile"): self.adjust_color([0,1,0])
                if(self.detected_class == "dangerous"): self.adjust_color([1,1,0])
                if(self.detected_class == "polluted"): self.adjust_color([1,0,0])
                sleep(2)
                self.adjust_color([0,1,1])
                # If requested, also inform the user via Telegram by transferring the modified model resulting image and the latest detected water quality class.
                if(notify == "Telegram" and self.detected_class != "empty"):
                    self.telegram_send_data("water_test", "6465514194", resulting_image)       
            # Stop the running inference.    
            finally:
                if(runner):
                    runner.stop()

    def make_a_get_request(self, com):
        # Depending on the given command, make an HTTP GET request to communicate with the web application.
        if(com == "csv"):
            # If requested, generate a CSV file from the ultrasonic scan information sent by Nano ESP32 — data records.
            req = requests.get(self.web_app + "generate.php?create=csv")
            if(req.status_code == 200):
                if(req.text.find("Server => ") > -1):
                    self.ultra_info_text.config(text="CSV file generated successfully!")
                    self.adjust_color([0,1,1])
                print("\n"+req.text)
            else:
                print("Server => Connection Error: " + str(req.status_code))
        elif(com == "get_model_result"):
            # If requested, get the latest neural network model detection result.
            # Then, convert the retrieved resulting data record to an ultrasonic (radar) image.
            req = requests.get(self.web_app + "generate.php?model_result=OK")
            if(req.status_code == 200):
                data_packet = req.text.split("_")
                self.latest_air_label = data_packet[0]
                data_record = data_packet[1]
                # Generate ultrasonic image.
                self.adjust_color([1,1,0])
                self.generate_ultrasonic_image(data_record)
                # Display the latest generated ultrasonic image with the detected air bubble class (label) for further inspection.
                self.ultrasonic_img.config(image="scans/latest_ultrasonic_image.jpg")
                self.ultra_info_text.config(text="Detected Class: " + self.latest_air_label)
            else:
                print("Server => Connection Error: " + str(req.status_code))
    
    def generate_ultrasonic_image(self, data_record, scanned_image_path="./scans/latest_ultrasonic_image.jpg"):
        x = 0
        y = 0
        # Get template image.
        template = cv2.imread(self.u_im["temp_path"])
        # Obtain the individual data points by decoding the passed data record.
        data_points = data_record.split(",")
        for point in data_points:
            # Draw depth indicators on the image template according to the given data point.
            p = float(point)*100
            if(p >= 15 and p < 20): cv2.rectangle(template, (x,y), (x+self.u_im["w"],y+self.u_im["h"]), (255,255,255), -1)
            if(p >= 20 and p < 25): cv2.rectangle(template, (x,y), (x+self.u_im["w"],y+self.u_im["h"]), (255,255,0), -1)
            if(p >= 25 and p < 30): cv2.rectangle(template, (x,y), (x+self.u_im["w"],y+self.u_im["h"]), (255,0,0), -1)
            if(p >= 30 and p < 35): cv2.rectangle(template, (x,y), (x+self.u_im["w"],y+self.u_im["h"]), (0,255,255), -1)
            if(p >= 35): cv2.rectangle(template, (x,y), (x + self.u_im["w"], y + self.u_im["h"]), (0,255,0), -1)
            # Configure coordinates.
            x += self.u_im["offset"]
            if(x == 400):
                x = 0
                y += self.u_im["offset"]
            print(str(x) + ", " + str(y))
        # Save the generated ultrasonic image.
        cv2.imwrite(scanned_image_path, template)
        print("\nUltrasonic image generated and saved successfully!")

    def telegram_send_data(self, com, chat_id, file_path="/scans/latest_ultrasonic_image.jpg"):
        # Get the file directory.
        _dir = os.path.abspath(os.getcwd())
        if(com == "ultrasonic"):
            path = self.telegram_webhook + "/sendPhoto"
            image_path = _dir + file_path
            # Make an HTTP POST request to transfer the generated ultrasonic image to the given Telegram bot via the Telegram Bot API.
            req = requests.post(path, data={"chat_id": chat_id, "caption": "🖼 Ultrasonic Image Received!\n\n📡 Detected Class: "+self.latest_air_label}, files={"photo": open(image_path, 'rb')})
            if(req.status_code == 200):
                self.adjust_color([0,1,0])
                self.ultra_info_text.config(text="Image transferred to the Telegram bot!")
                print("\nImage transferred to the Telegram bot!")
            else:
                print("Server => Connection Error: " + str(req.status_code))
        if(com == "water_test"):
            path = self.telegram_webhook + "/sendPhoto"
            image_path = _dir + file_path
            # Make an HTTP POST request to transfer the model resulting image modified with the passed bounding boxes to the given Telegram bot via the Telegram Bot API.
            req = requests.post(path, data={"chat_id": chat_id, "caption": "🤖 Inference running successfully!\n\n💧 Detected Class: " + self.detected_class}, files={"photo": open(image_path, 'rb')})
            if(req.status_code == 200):
                self.adjust_color([0,1,0])
                self.cam_info_text.config(text="Image[{}] sent to Telegram!".format(self.detected_class))
                print("\nModel resulting image transferred to the Telegram bot!")
                sleep(2)
                self.adjust_color([0,1,1])
            else:
                print("Server => Connection Error: " + str(req.status_code))

    def display_camera_feed(self):
        # Display the real-time video stream generated by the USB camera.
        ret, img = self.camera.read()
        # Resize the captured frame depending on the given object detection model.
        self.latest_frame_m = cv2.resize(img, self.frame_size_m)
        # Resize the same frame to display it on the UNIHIKER screen (snapshot).
        self.latest_frame_s = cv2.resize(img, self.frame_size_s)
        # Stop the camera feed if requested.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.camera.release()
            cv2.destroyAllWindows()
            print("\nCamera Feed Stopped!")
    
    def take_snapshot(self, filename="assets/snapshot.jpg"):
        # Show the latest camera frame (snapshot) on UNIHIKER to inform the user.
        cv2.imwrite("./"+filename, self.latest_frame_s)
        self.cam_snapshot_img.config(image=filename)
        # Store the latest modified image sample on the memory.
        self.modified_image = self.latest_frame_m
    
    def save_img_sample(self, given_class):
        if(given_class > -1):
            # Create the file name for the image sample.
            date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = "IMG_{}_{}.jpg".format(self.class_names[given_class], date)
            # Save the modified image sample.
            cv2.imwrite("./samples/"+filename, self.modified_image)
            print("\nSample Saved Successfully: ./samples/" + filename)
            # Notify the user.
            self.cam_info_text.config(text="Saved: "+filename)
        else:
            self.cam_info_text.config(text="Please select a class.")
        
    def camera_feed(self):
        # Start the camera feed loop.
        while True:
            self.display_camera_feed()
    
    def create_user_interface(self, _x=120, _y=10, offset=15, origin="top_left"):
        # Design the user interface (GUI) via the built-in unihiker module.
        # Camera interface for AI-based chemical water quality test.
        self.cam_backg = self.interface.fill_rect(x=0, y=0, w=240, h=320, color="#9BB5CE")
        self.cam_snapshot_img = self.interface.draw_image(x=60, y=5, image="assets/cam_wait.jpg", origin=origin, onclick=lambda:self.interface_config("clear_class"))
        self.cam_section = self.interface.fill_round_rect(x=5, y=130, r=10, w=230, h=185, color="#215E7C")
        self.cam_run_button = self.interface.fill_round_rect(x=45, y=250, r=5, w=150, h=45, color="#FAE0D8", onclick=self.run_inference)
        self.cam_run_text = self.interface.draw_text(x=120, y=272, text="Run Inference", origin="center", color="#5C5B57", font_size=12, onclick=self.run_inference)
        self.cam_save_button = self.interface.fill_round_rect(x=45, y=195, r=5, w=150, h=45, color="#FAE0D8", onclick=lambda:self.save_img_sample(self.selected_class))
        self.cam_save_text = self.interface.draw_text(x=120, y=217, text="Capture Sample", origin="center", color="#5C5B57", font_size=12, onclick=lambda:self.save_img_sample(self.selected_class))
        self.cam_snap_button = self.interface.fill_round_rect(x=45, y=140, r=5, w=150, h=45, color="#FAE0D8", onclick=self.take_snapshot)
        self.cam_snap_text = self.interface.draw_text(x=120, y=162, text="Snapshot", origin="center", color="#5C5B57", font_size=12)
        self.cam_info_text = self.interface.draw_text(x=120, y=305, text="Pending...", origin="center", color="white", font_size=8)
        # Elements and coordinates — Camera. 
        self.cam_int_vars = [self.cam_backg, self.cam_snapshot_img, self.cam_section, self.cam_run_button, self.cam_run_text, self.cam_save_button, self.cam_save_text, self.cam_snap_button, self.cam_snap_text, self.cam_info_text]
        self.cam_int_vals = [0, 60, 5, 45, 120, 45, 120, 45, 120, 120]
        # Ultrasonic sensor interface for AI-based ultrasonic imaging.
        self.ultra_backg = self.interface.fill_rect(x=0, y=0, w=240, h=320, color="#5C5B57")
        self.ultrasonic_img = self.interface.draw_image(x=20, y=0, image="assets/ultrasonic_temp.jpg", origin=origin, onclick=lambda:self.telegram_send_data("ultrasonic", "6465514194"))
        self.ultra_section = self.interface.fill_round_rect(x=5, y=205, r=10, w=230, h=110, color="#F9E5C9")
        self.ultra_ins_button = self.interface.fill_round_rect(x=45, y=260, r=5, w=150, h=35, color="#F5F5F0", onclick=lambda:self.make_a_get_request("get_model_result"))
        self.ultra_ins_text = self.interface.draw_text(x=120, y=277, text="Generate Image", origin="center", color="#5C5B57", font_size=12, onclick=lambda:self.make_a_get_request("get_model_result"))
        self.ultra_gen_button = self.interface.fill_round_rect(x=45, y=215, r=5, w=150, h=35, color="#F5F5F0", onclick=lambda:self.make_a_get_request("csv"))
        self.ultra_gen_text = self.interface.draw_text(x=120, y=232, text="Generate CSV", origin="center", color="#5C5B57", font_size=12, onclick=lambda:self.make_a_get_request("csv"))
        self.ultra_info_text = self.interface.draw_text(x=120, y=305, text="Pending...", origin="center", color="#5C5B57", font_size=8)
        # Elements and coordinates — Ultrasonic Sensor.
        self.ultra_int_vars = [self.ultra_backg, self.ultrasonic_img, self.ultra_section, self.ultra_ins_button, self.ultra_ins_text, self.ultra_gen_button, self.ultra_gen_text, self.ultra_info_text]
        self.ultra_int_vals = [0, 20, 5, 45, 120, 45, 120, 120]
        # Home screen.
        self.main_backg = self.interface.draw_image(x=0, y=0, image="assets/background.jpg", origin=origin, onclick=lambda:self.adjust_color([0,0,0]))
        self.main_ultra_button = self.interface.fill_round_rect(x=20, y=10, r=5, w=200, h=45, color="#5C5B57", onclick=lambda:self.interface_config("ultra"))
        self.main_ultra_text = self.interface.draw_text(x=120, y=32, text="Aquatic Ultrasonic Scan", origin="center", color="white", font_size=12, onclick=lambda:self.interface_config("ultra"))
        self.main_cam_button = self.interface.fill_round_rect(x=20, y=265, r=5, w=200, h=45, color="#9BB5CE", onclick=lambda:self.interface_config("cam"))
        self.main_cam_text = self.interface.draw_text(x=120, y=287, text="Water Quality Test", origin="center", color="white", font_size=12, onclick=lambda:self.interface_config("cam"))
        # Elements and coordinates — Home Screen.
        self.home_int_vars = [self.main_backg, self.main_ultra_button, self.main_ultra_text, self.main_cam_button, self.main_cam_text]
        self.home_int_vals = [0, 20, 120, 20, 120]
        
    def board_configuration(self):
        # Utilize the integrated sensors on UNIHIKER to provide a feature-rich user experience.
        while True:
            # If the control button A is pressed, return to the home screen.
            if button_a.is_pressed() == True:
                self.interface_config("home")
                sleep(1)
            # If the control button B is pressed, change the selected class.
            if button_b.is_pressed() == True:
                self.selected_class+=1
                if self.selected_class == 3:
                    self.selected_class = 0
                self.cam_save_button.config(color=self.class_colors[self.selected_class])
                if(self.selected_class == 0): self.adjust_color([0,1,0])
                if(self.selected_class == 1): self.adjust_color([1,1,0])
                if(self.selected_class == 2): self.adjust_color([1,0,0])
                sleep(1)
    
    def interface_config(self, con, _hide=350):
        if(con == "home"):
            for i in range(len(self.home_int_vals)):
                self.home_int_vars[i].config(x=self.home_int_vals[i])
            for i in range(len(self.cam_int_vals)):
                self.cam_int_vars[i].config(x=_hide)
            for i in range(len(self.ultra_int_vals)):
                self.ultra_int_vars[i].config(x=_hide)
            self.adjust_color([0,0,0])
        elif(con == "cam"):
            for i in range(len(self.home_int_vals)):
                self.home_int_vars[i].config(x=_hide)
            for i in range(len(self.cam_int_vals)):
                self.cam_int_vars[i].config(x=self.cam_int_vals[i])
            for i in range(len(self.ultra_int_vals)):
                self.ultra_int_vars[i].config(x=_hide)
            self.adjust_color([0,1,1])
        elif(con == "ultra"):
            for i in range(len(self.home_int_vals)):
                self.home_int_vars[i].config(x=_hide)
            for i in range(len(self.cam_int_vals)):
                self.cam_int_vars[i].config(x=_hide)
            for i in range(len(self.ultra_int_vals)):
                self.ultra_int_vars[i].config(x=self.ultra_int_vals[i])
            self.adjust_color([1,0,1])
        elif(con == "clear_class"):
            self.selected_class = -1
            self.cam_save_button.config(color="#FAE0D8")
            self.cam_info_text.config(text="Pending...")
            self.adjust_color([0,0,0])

    def adjust_color(self, color):
        self.rgb["r"].write_digital(1-color[0])
        self.rgb["g"].write_digital(1-color[1])
        self.rgb["b"].write_digital(1-color[2])

import sys
import numpy as np
import image_handler
import json
from PIL import Image
import time
class MainApp:
    def __init__(self,json_input=None):
        self.json_input=json_input
        from modelTorch import  ModelHandler
        from image_handler import ImageHandler
        self.model_handler:ModelHandler = ModelHandler(self)
        self.image_handler:ImageHandler = ImageHandler(self)
        self.game_id = ""
        self.while_loop = True
        self.pause_state = False
        self.min_size = 10
        self.max_size = 40
        self.img_tolerant = 65
        self.size = 30
        self.h_pic = 720
        self.w_pic = 1280


        self.pusto = []
        self.mask = []
        self.list_bb = []
        self.list_clast = []
        self.short_list_bb = []
        self.canvFull = Image.new('RGBA', (self.w_pic, self.h_pic), 'black')


        self.list_ball_BB = []
        self.ball_coord = {'x': 0, 'y': 0}
        self.old_ball_coord = {'x': 0, 'y': 0}
        self.speed = {'x': 0, 'y': 0}
        self.players_list = []

        self.min_y = 0
        self.bc = 0
        self.hc = 0
        self.fc = 0
        self.json_input = {}

    def find_min_y(self):
        mask=self.mask
        if isinstance(self.mask,Image.Image):
            # Convert the PIL Image to a numpy array
            mask = np.array(self.mask)

        # Assuming the image is grayscale, you can work with it as a 2D array
        height, width = mask.shape

        for i in range(height):
            for j in range(width):
                if mask[i, j] > 0:
                    self.min_y = i
                    return  # Exit the method once the first non-zero pixel is found

    def main_loop(self, model_name):
        self.model_handler.load_model(model_name)
        self.find_min_y()
        print("Server ready!")

        while self.while_loop:
            # Resetting variables, similar to the JS logic
            self.list_bb = []
            self.short_list_bb = []
            self.speed['x'] = self.ball_coord['x'] - self.old_ball_coord['x']
            self.speed['y'] = self.ball_coord['y'] - self.old_ball_coord['y']
            self.old_ball_coord = self.ball_coord
            self.ball_coord = {'x': 0, 'y': 0}
            # players_list = []
            self.bc = 0
            self.hc = 0
            self.fc = 0

            if not self.pause_state:
                # Logic for image processing, marking, detection...
                image =self.image_handler.get_img()
                markimg = self.image_handler.pic_mark(image[:])
                self.image_handler.mark_bb(markimg)
                print("mark", len(self.list_bb))
                self.model_handler.mass_detect(image)
            else:
                self.send_data()


            time.sleep(2)  # Equivalent to await sleep(2000)

    def check_distance(self, bb, old_coord):
        # Assuming bb has 'xc' and 'yc' as x and y coordinates of the bounding box center
        dx = bb['xc'] - old_coord['x']
        dy = bb['yc'] - old_coord['y']
        return (dx ** 2 + dy ** 2) ** 0.5  # Euclidean distance

    def start_check(self):
        print(f"detect: {self.bc}, {self.hc}, {self.fc}")
        self.image_handler.claster()

        dm = 100000
        for bb in self.short_list_bb:
            if bb['t'] == 2 and self.bc == 1:
                self.ball_coord['x'] = bb['xc']
                self.ball_coord['y'] = bb['yc']

            d = self.check_distance(bb, self.old_ball_coord)
            if self.bc == 0 and d < dm and bb['t'] != 0:
                dm = d
                self.ball_coord['x'] = bb['xc']
                self.ball_coord['y'] = bb['yc']

        if self.ball_coord['x'] == 0:
            self.ball_coord['x'] = self.old_ball_coord['x'] + self.speed['x'] / 2
            self.ball_coord['y'] = self.old_ball_coord['y'] + self.speed['y'] / 2

        if self.bc > 0:
            print(f"ball found: {self.ball_coord}")
        else:
            print(f"ball NOT found: {self.ball_coord}, {self.bc}, {self.hc}")

        self.send_data()

    def send_data(self):
        r = {
            "GameID": self.game_id,
            "ball_coord": self.ball_coord,
            "head": [],  # based on your logic
            "claster": [],  # based on your logic
            "ballfound": self.bc == 1,
            "pauseState": self.pause_state,
            "full": []  # based on your logic
        }

        # Logic to populate the "head", "claster", and "full" fields goes here
        for i in range(len(listClast)):
            if listClast[i]['t'] > 0:
                r['claster'].append({
                    'x': listClast[i]['x'],
                    'y': listClast[i]['y'],
                    'w': listClast[i]['w'],
                    'h': listClast[i]['h'],
                })

        for i in range(len(shortListBB)):
            if shortListBB[i]['t'] == 3:
                r['head'].append({
                    'x': shortListBB[i]['xc'],
                    'y': shortListBB[i]['yc'],
                })
        response = requests.post(self.json_input['zoneAdr'], json=r)
        print("Data sent:", response.text)

    def load_json(self, json_input=None):
        if not json_input:
            # I'm not sure what the equivalent of process.argv[2] is in your context.
            # Assuming you're using argparse or sys.argv:
            json_input=sys.argv[2]
        print("load:", json_input)
        with open(json_input, 'r') as file:
            self.json_input = json_input = json.load(file)
        self.game_id = json_input['gameId']
        print(json_input)
        self.w_pic = json_input['width']
        self.h_pic = json_input['height']
        self.min_size = json_input['minSize']
        self.max_size = json_input['maxSize']

        # Create a blank white image with Pillow
        self.canvFull = Image.new('RGBA', (self.w_pic, self.h_pic), 'white')

        # Load mask and pusto using PIL
        self.mask = np.array(Image.open(json_input['mask']).convert('L'))  # Convert to grayscale
        self.pusto = np.array(Image.open(json_input['pusto']))

        # No need for 'ctx' or 'mydata' when using PIL

        self.main_loop(json_input['baseName'])
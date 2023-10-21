import os.path

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
import numpy as np
from app import MainApp

size = 30  # From the provided code

class CustomModel(nn.Module):
    def __init__(self):
        super(CustomModel, self).__init__()
        self.norm = nn.BatchNorm2d(3)
        self.conv1 = nn.Conv2d(3, 16, kernel_size=5, stride=1, padding='same')
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        self.dropout1 = nn.Dropout(0.1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=1, padding='same')
        self.dropout2 = nn.Dropout(0.1)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=2, stride=1)
        self.fc1 = nn.Linear(64*6*6, 64)  # Assuming size reduces to 6x6 after all convolutions
        self.dropout3 = nn.Dropout(0.5)
        self.fc2 = nn.Linear(64, 5)

    def forward(self, x):
        x = self.norm(x)
        x = F.relu(self.conv1(x))
        x = self.pool(x)
        x = self.dropout1(x)
        x = F.relu(self.conv2(x))
        x = self.pool(x)
        x = self.dropout2(x)
        x = F.relu(self.conv3(x))
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout3(x)
        x = F.softmax(self.fc2(x), dim=1)
        return x

class ModelHandler:
    def __init__(self, app:MainApp):
        self.model = CustomModel()
        self.app = app
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.CrossEntropyLoss()

    def load_model(self, name):
        if os.path.exists(name):
            self.model.load_state_dict(torch.load(name + ".pth"))
        else:
            print('There is no model',name)

    def compile_model(self):  # In PyTorch, we don't compile the model in the same way as Keras
        pass

    def detect(self, bb, n, canv_full):
        # Using PIL for image operations
        image = Image.fromarray(canv_full)
        cropped = image.crop((bb['x'], bb['y'], bb['x'] + bb['w'], bb['y'] + bb['h']))
        cropped.show()  # Display the cropped image
        resized = cropped.resize((self.app.size, self.app.size))
        resized.show()  # Display the resized image

        img_np = np.array(resized).transpose((2, 0, 1))
        img_tensor = torch.tensor(img_np).float().unsqueeze(0)
        prediction = self.model(img_tensor)
        _, predicted = torch.max(prediction, 1)
        ii = predicted.item()
        return ii, n

    def mass_detect(self,canv_full):
        cc = 0

        for i, bb in enumerate(self.app.list_bb):
            ii, _ = self.detect(bb, i, canv_full)
            self.app.list_bb[i]['t'] = ii

            if ii == 2:
                self.app.bc += 1
                self.app.short_list_bb.append(bb)
                if self.app.ball_coord['x'] == 0 and self.app.ball_coord['y'] == 0:
                    self.app.ball_coord['x'] = bb['xc']
                    self.app.ball_coord['y'] = bb['yc']
            if ii == 3:
                self.app.hc += 1
            if ii == 4:
                self.app.fc += 1

            if ii == 2 or ii == 3 or ii == 4 or self.app.list_bb[v.n].checkDistans(self.app.old_ball_coord.x, sef.app.old_ball_coord.y, 100):
                self.app.short_list_bb.apeend(self.app.list_bb[v.n])

            if (cc == len(self.app.list_bb)):
                print("found", self.app.bc, self.app.hc, self.app.fc)
                self.app.start_check()

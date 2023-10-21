import tensorflow as tf
import numpy as np
from PIL import Image
import asyncio
from app import MainApp
size = 30  # From the provided code

class ModelHandler:
    def __init__(self,app:MainApp):
        self.model = tf.keras.Sequential()
        self.app=app
        self._initialize_model()

    def _initialize_model(self):
        self.model.add(tf.keras.layers.BatchNormalization(input_shape=[size, size, 3]))
        self.model.add(tf.keras.layers.Conv2D(strides=1, kernel_size=5, filters=16, padding="same",
                                              kernel_initializer="varianceScaling", activation="relu"))
        self.model.add(tf.keras.layers.MaxPooling2D(strides=2, pool_size=2))
        self.model.add(tf.keras.layers.Dropout(0.1))
        self.model.add(tf.keras.layers.Conv2D(strides=1, kernel_size=3, filters=32, padding="same", activation="relu"))
        self.model.add(tf.keras.layers.MaxPooling2D(strides=2, pool_size=2))
        self.model.add(tf.keras.layers.Dropout(0.1))
        self.model.add(tf.keras.layers.Conv2D(strides=1, kernel_size=2, filters=64, padding="valid", activation="relu"))
        self.model.add(tf.keras.layers.Flatten())
        self.model.add(tf.keras.layers.Dense(64, activation="relu"))
        self.model.add(tf.keras.layers.Dropout(0.5))
        self.model.add(tf.keras.layers.Dense(5, kernel_initializer="varianceScaling", activation="softmax"))

    def load_model(self, name):
        self.model = tf.keras.models.load_model(name + ".pth")
        self.compile_model()

    def compile_model(self):
        self.model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        print("Model loaded and compiled")
        self.model.summary()

    def detect(self, bb, n, canv_full):
        # Using PIL for image operations
        image = Image.fromarray(canv_full)
        cropped = image.crop((bb['x'], bb['y'], bb['x'] + bb['w'], bb['y'] + bb['h']))
        resized = cropped.resize((self.app.size, self.app.size))
        img_np = np.array(resized)
        r = img_np.reshape(1, self.size, self.size, 3)

        prediction = self.model.predict(r)
        ii = np.argmax(prediction)
        return ii, n

    def mass_detect(self, list_bb, canv_full):
        cc=0

        for i, bb in enumerate(list_bb):
            ii, _ =  self.detect(bb, i, canv_full)
            list_bb[i]['t'] = ii

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

            if ii == 2 or ii == 3 or ii == 4 or list_bb[v.n].checkDistans(self.app.old_ball_coord.x, sef.app.old_ball_coord.y, 100):
                self.app.short_list_bb.apeend(list_bb[v.n])

            if (cc == len(self.app.list_bb)):
                print("found", self.app.bc, self.app.hc, self.app.fc)
                self.app.start_check()

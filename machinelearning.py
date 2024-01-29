import cv2  # Import OpenCV library for image and video processing
from pyzbar import pyzbar  # Import pyzbar library for barcode decoding
import speech_recognition as sr
from bidi.algorithm import get_display
import arabic_reshaper
import io
from flask import Flask, request, redirect
from flask_restful import Resource, Api
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
api = Api(app)
charset='utf-8'


def read_barcodes(frame):
    """
    Detects and decodes barcodes from a video frame.

    Args:
        frame: A video frame captured from the camera.

    Returns:
        The processed frame with bounding boxes drawn around detected barcodes.
    """

    barcodes = pyzbar.decode(frame)  # Decode barcodes in the frame
    barcode_text = 0
    for barcode in barcodes:
        x, y, w, h = barcode.rect  # Extract barcode coordinates
        barcode_text = barcode.data.decode('utf-8') # Decode barcode data
        print(barcode_text)  # Print decoded text to console
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)  # Draw green rectangle around barcode
    return frame,barcode_text

class barcode_reader(Resource): 

    def get(self):
        """
        Initializes the camera, captures and processes frames for barcode detection, and displays the results.
        """

        camera = cv2.VideoCapture(0)  # Open default camera

        ret, frame = camera.read()  # Read initial frame

        
        while ret:  # Loop while frames are being captured successfully
            ret, frame = camera.read()  # Capture new frame
            frame,barcode = read_barcodes(frame)  # Process frame for barcode detection
            cv2.imshow('Barcode Reader', frame)  # Display frame with detected barcodes
            if barcode != 0 :
                return {"Barcode": barcode}
            if cv2.waitKey(1) & 0xFF == 27:  # Exit loop if 'Esc' key is pressed
                 break
            
        
        camera.release()  # Release camera resources
        cv2.destroyAllWindows()  # Close all open windows


class voice_search(Resource):
    def get(self):
        r = sr.Recognizer()

        with sr.Microphone() as src:
            print('Say something...')
            r.adjust_for_ambient_noise(src, duration=1)  # Adjust for noise
            audio = r.listen(src)
            
        try:
            # Recognize speech and handle Arabic text appropriately
            recognized_text = r.recognize_google(audio, language='ar-AR',show_all = True)
            recognized_text = recognized_text['alternative'][0].get('transcript')
            reshaped_text = arabic_reshaper.reshape(recognized_text)  # Reshape Arabic letters
            bidi_text = get_display(reshaped_text)  # Apply BiDi formatting
            print(bidi_text.lower())
            return {"Text": str(bidi_text.lower())} # Convert to lowercase for consistency

        except sr.UnknownValueError:
            return {"Error": "Could not understand audio"}
        except sr.RequestError as e:
            return {"Error": "Could not request results from Google Speech Recognition service; {0}".format(e)}



api.add_resource(barcode_reader,'/barcodereader')
api.add_resource(voice_search,'/voicesearch')

   
if __name__ == "__main__":
    app.config['JSON_AS_ASCII'] = False
    app.run(debug=True)


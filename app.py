import os
import base64
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from gradio_client import Client, handle_file

app = Flask(__name__)
CORS(app) # Taaki aapki WordPress site isse baat kar sake

# Hugging Face ka Free Server (IDM-VTON) connect kar rahe hain
print("Hugging Face API se connect ho raha hai, kripya pratiksha karein...")
client = Client("yisol/IDM-VTON")

def save_base64_to_temp(base64_data):
    """Base64 image ko temporary file mein save karta hai taaki AI ko bhej sakein."""
    if "," in base64_data:
        header, encoded = base64_data.split(",", 1)
    else:
        encoded = base64_data
    
    file_data = base64.b64decode(encoded)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    temp_file.write(file_data)
    temp_file.close()
    return temp_file.name

@app.route('/api/try-on', methods=['POST'])
def virtual_try_on():
    person_img_path = None
    cloth_img_path = None
    try:
        data = request.json
        person_image_b64 = data.get('person_image') # User ki photo
        cloth_image_b64 = data.get('cloth_image')   # Kapde ki photo

        print("Hugging Face (Free AI) ko request bhej rahe hain. Isme 1-2 minute lag sakte hain...")
        
        # Images ko temporary file mein save karein
        person_img_path = save_base64_to_temp(person_image_b64)
        cloth_img_path = save_base64_to_temp(cloth_image_b64)

        # Gradio (Hugging Face) API ko call bhej rahe hain
        result = client.predict(
            {"background": handle_file(person_img_path), "layers": [], "composite": None},
            handle_file(cloth_img_path),
            "a piece of clothing", # Description
            True,  # is_checked
            True,  # is_checked_crop
            30,    # denoise steps
            42,    # seed
            api_name="/tryon"
        )
        
        # AI ne jo image banayi hai, uski file path nikal rahe hain
        output_image_path = result[0] 
        
        # Us image ko wapas Base64 mein convert kar rahe hain taaki website par dikha sakein
        with open(output_image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            final_b64_url = f"data:image/png;base64,{encoded_string}"
        
        print("Success: Free AI ne Image successfully generate kar di!")
        return jsonify({"output_image_url": final_b64_url})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Pura hone ke baad kachra (temp files) delete kar dein
        if person_img_path and os.path.exists(person_img_path):
            os.remove(person_img_path)
        if cloth_img_path and os.path.exists(cloth_img_path):
            os.remove(cloth_img_path)

if __name__ == '__main__':
    print("Backend Server chalu ho gaya hai! http://localhost:5000 par run kar raha hai.")
    app.run(host='0.0.0.0', port=5000)

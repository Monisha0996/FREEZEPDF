from flask import Flask, render_template, request, send_file, jsonify
from io import BytesIO
import fitz  # PyMuPDF
from PIL import Image

app = Flask(__name__)

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/convert', methods=['POST'])
def convert_pdf_to_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        # Open the PDF file with PyMuPDF
        pdf_document = fitz.open(stream=file.read(), filetype='pdf')
        
        # Create a new PDF with the images
        output_pdf = BytesIO()
        pdf_writer = fitz.open()
        
        # Set the desired DPI for higher quality
        zoom_x = 2.0  # Increase for higher horizontal resolution (200%)
        zoom_y = 2.0  # Increase for higher vertical resolution (200%)
        matrix = fitz.Matrix(zoom_x, zoom_y)  # Define the transformation matrix
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap(matrix=matrix, alpha=False)  # Render page to an image with higher resolution
            
            # Convert the Pixmap to an image format supported by PIL
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Save the image to a BytesIO object with higher DPI
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG', dpi=(600, 600))  # Save with 600 DPI for high quality
            img_byte_arr.seek(0)
            
            # Insert the image into a new PDF page
            img_pdf = fitz.open()
            rect = fitz.Rect(0, 0, img.width, img.height)
            page = img_pdf.new_page(width=rect.width, height=rect.height)
            page.insert_image(rect, stream=img_byte_arr)
            pdf_writer.insert_pdf(img_pdf)
        
        # Save the generated PDF to a BytesIO object
        pdf_writer.save(output_pdf)
        output_pdf.seek(0)
        
        return send_file(output_pdf, as_attachment=True, download_name="output.pdf", mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')

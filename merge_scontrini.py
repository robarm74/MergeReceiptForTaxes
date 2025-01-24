from flask import Flask, render_template, request, send_file, jsonify
import os
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
from rectpack import newPacker

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'static'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['OUTPUT_FOLDER']):
    os.makedirs(app.config['OUTPUT_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'success': True, 'filename': filename})
    return jsonify({'error': 'Invalid file type'})










class Scontrino:
    def __init__(self, larghezza, altezza, filename):
        self.larghezza = larghezza
        self.altezza = altezza
        self.filename = filename


def ridimensiona_scontrino(receipt_path, target_width_pts, fattura_width_pts):
    """Ridimensiona un singolo scontrino in base alle dimensioni target."""
    with fitz.open(receipt_path) as receipt_doc:
        receipt_page = receipt_doc[0]
        rect = receipt_page.rect

        if 'fattura' in os.path.basename(receipt_path).lower():
            scale = fattura_width_pts / min(rect.width, rect.height)
        else:
            scale = target_width_pts / min(rect.width, rect.height)

        new_width = rect.width * scale
        new_height = rect.height * scale
        return new_width, new_height


@app.route('/generate', methods=['POST'])
@app.route('/generate', methods=['POST'])
def generate_pdf():
    files = request.json.get('files', [])
    spacing = request.json.get('spacing', 10)

    if not files:
        return jsonify({'error': 'No files selected'})

    # Costanti
    a4_width, a4_height = 595, 842  # Dimensioni A4 in punti
    target_width_mm = 76
    fattura_width_mm = 200
    mm_to_points = 2.83465  # Conversione millimetri a punti
    target_width_pts = target_width_mm * mm_to_points
    fattura_width_pts = fattura_width_mm * mm_to_points

    
    

    scontrini = []

    # Ridimensiona tutti gli scontrini
    for filename in files:
        receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        new_width, new_height = ridimensiona_scontrino(receipt_path, target_width_pts, fattura_width_pts)

        # Aggiungi margini di separazione
        new_width += spacing
        new_height += spacing

        scontrini.append(Scontrino(new_width, new_height, filename))

    # Inizializza il packer
    packer = newPacker(rotation=True)  # Abilita la rotazione

    # Aggiungi un bin con dimensioni A4 (numero illimitato di fogli)
    packer.add_bin(a4_width, a4_height, float("inf"))

    # Aggiungi gli scontrini come rettangoli
    for scontrino in scontrini:
        packer.add_rect(scontrino.larghezza, scontrino.altezza, rid=scontrino.filename)

    # Esegui il packing
    packer.pack()

    # Crea il PDF finale
    output_pdf = fitz.open()

    # Itera sui fogli generati
    for bin_index, bin in enumerate(packer):
        page = output_pdf.new_page(width=a4_width, height=a4_height)

        for rect in bin:
            scontrino = next(s for s in scontrini if s.filename == rect.rid)
            receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], scontrino.filename)

            # Controlla se il rettangolo è stato ruotato
            rotated = rect.width != scontrino.larghezza

            with fitz.open(receipt_path) as receipt_doc:
                receipt_page = receipt_doc[0]

                # Calcola il rettangolo di destinazione
                target_rect = fitz.Rect(
                    rect.x, rect.y,
                    rect.x + (rect.width - spacing),
                    rect.y + (rect.height - spacing),
                )

                # Posiziona la pagina PDF originale, ruotandola se necessario
                if rotated:
                    page.show_pdf_page(target_rect, receipt_doc, 0, rotate=90)
                else:
                    page.show_pdf_page(target_rect, receipt_doc, 0)

    # Salva il PDF di output
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'output.pdf')
    output_pdf.save(output_path)
    output_pdf.close()

    return jsonify({'success': True, 'pdf_url': '/static/output.pdf'})












if __name__ == '__main__':
    app.run(debug=True)
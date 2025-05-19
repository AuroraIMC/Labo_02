#Codigo desarrollado por aurora matamoros
#app que hace una detecion de plagio usando las siguientes librerias y da un grafco.
from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import pdfplumber  
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt
from collections import Counter

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")
 
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

app = Flask(__name__)
app.secret_key = 'clave-secreta'

# Carpeta donde se guardan los PDFs subidos
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Funciones 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extraer_texto_pdf(ruta_pdf):
    texto = ""
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text()
    return texto

def limpiar_y_tokenizar(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-záéíóúüñ0-9\s]', '', texto)
    # Tokenizar
    tokens = word_tokenize(texto, language='spanish')
    # Eliminar stopwords en español
    stop_words = set(stopwords.words('spanish'))
    palabras_limpias = [palabra for palabra in tokens if palabra not in stop_words]

    return palabras_limpias

def riqueza_lexica(lista_palabras):
    total = len(lista_palabras)
    unicas = len(set(lista_palabras))
    if total == 0:
        return 0
    return unicas / total

def graficar_frecuencias(tokens1, tokens2, nombre1="PDF 1", nombre2="PDF 2"):
    # Contar las palabras más comunes
    top1 = Counter(tokens1).most_common(10)
    top2 = Counter(tokens2).most_common(10)

    palabras1, frecs1 = zip(*top1)
    palabras2, frecs2 = zip(*top2)

    fig, axs = plt.subplots(1, 2, figsize=(14, 6))

    axs[0].bar(palabras1, frecs1, color='steelblue')
    axs[0].set_title(f'Top 10 palabras - {nombre1}')
    axs[0].tick_params(axis='x', rotation=45)

    axs[1].bar(palabras2, frecs2, color='salmon')
    axs[1].set_title(f'Top 10 palabras - {nombre2}')
    axs[1].tick_params(axis='x', rotation=45)

    plt.tight_layout()

    # Guardar el gráfico en static/
    ruta = os.path.join('static', 'grafico.png')
    plt.savefig(ruta)
    plt.close()

def calcular_similitud_ngramas(tokens1, tokens2, n=3):
    def obtener_ngramas(lista, n):
        return list(zip(*[lista[i:] for i in range(n)]))

    ngramas1 = obtener_ngramas(tokens1, n)
    ngramas2 = obtener_ngramas(tokens2, n)

    if not ngramas1 or not ngramas2:
        return 0.0

    set1 = set(ngramas1)
    set2 = set(ngramas2)

    interseccion = set1.intersection(set2)
    union = set1.union(set2)

    similitud = len(interseccion) / len(union)
    return similitud * 100  # en porcentaje


#parte que une todo
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file1 = request.files.get('pdf1')
        file2 = request.files.get('pdf2')

        if not file1 or not allowed_file(file1.filename):
            flash('Falta el primer archivo o no es un PDF.')
            return redirect(request.url)
        if not file2 or not allowed_file(file2.filename):
            flash('Falta el segundo archivo o no es un PDF.')
            return redirect(request.url)

        filename1 = secure_filename(file1.filename)
        filename2 = secure_filename(file2.filename)

        path1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
        path2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)

        file1.save(path1)
        file2.save(path2)

        # Extraer texto con pdfplumber
        texto1 = extraer_texto_pdf(path1)
        texto2 = extraer_texto_pdf(path2)
        # Tokenisa
        tokens1 = limpiar_y_tokenizar(texto1)
        tokens2 = limpiar_y_tokenizar(texto2)
        # Riqueza lexica
        riqueza1 = riqueza_lexica(tokens1)
        riqueza2 = riqueza_lexica(tokens2)
        # Plot
        graficar_frecuencias(tokens1, tokens2)
        riqueza1 = riqueza_lexica(tokens1)
        riqueza2 = riqueza_lexica(tokens2)
        
        print("Texto del PDF 1:", texto1[:200])
        print("Texto del PDF 2:", texto2[:200])
        print("Palabras limpias del PDF 1:", tokens1[:20])
        print("Palabras limpias del PDF 2:", tokens2[:20])
        flash('¡Archivos cargados y texto extraído correctamente!')
        print(f'Riqueza léxica PDF 1: {riqueza1:.3f}')
        print(f'Riqueza léxica PDF 2: {riqueza2:.3f}')
        flash(f'Riqueza léxica del PDF 1: {riqueza1:.3f}')
        flash(f'Riqueza léxica del PDF 2: {riqueza2:.3f}')
        similitud = calcular_similitud_ngramas(tokens1, tokens2, n=3)
        flash(f'Similitud estimada por trigramas: {similitud:.2f}%')
        print(f'Similitud por n-gramas: {similitud:.2f}%')

    return render_template('index.html')

# Sin esto  no funciona
if __name__ == '__main__':
    app.run(debug=True)

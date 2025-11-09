from flask import Flask, send_file, request, abort
from scraper import extrair_boletim  # sua função que retorna o caminho absoluto do xlsx

app = Flask(__name__)
TOKEN = "MEU_TOKEN"  # coloque algo forte

@app.route('/gerar', methods=['GET'])
def gerar():
    token = request.args.get('token') or request.headers.get('Authorization')
    if token != TOKEN and token != f"Bearer {TOKEN}":
        abort(401)
    # extrair_boletim() salva e retorna DataFrame; adapte pra retornar caminho absoluto do xlsx
    xlsx_path = extrair_boletim()  # modifique sua função para retornar caminho absoluto do xlsx gerado
    return send_file(xlsx_path, as_attachment=True, download_name=xlsx_path.split("/")[-1])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

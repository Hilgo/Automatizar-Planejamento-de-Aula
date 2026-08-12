import json
import os
import shutil
import tempfile
from pathlib import Path

from authlib.integrations.flask_client import OAuth
from flask import Flask, after_this_request, flash, redirect, render_template, request, send_file, session, url_for
from werkzeug.utils import secure_filename

from planejamento import generate_planning_from_dict

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-para-uma-segura")

oauth = OAuth(app)
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    api_base_url="https://www.googleapis.com/oauth2/v2/",
    client_kwargs={"scope": "openid email profile"},
)

ALLOWED_EXTENSIONS = {"json", "xlsx"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize_file_name(filename: str) -> str:
    return secure_filename(filename)


def oauth_configured() -> bool:
    return bool(os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"))


def find_uploaded_file(uploaded_files: dict, expected_path: str) -> Path | None:
    expected_name = Path(expected_path).name
    expected_secure = secure_filename(expected_name)

    for name, file in uploaded_files.items():
        if name == expected_name or name == expected_secure:
            return file

    for name, file in uploaded_files.items():
        if name.lower() == expected_name.lower() or name.lower() == expected_secure.lower():
            return file

    return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "user" not in session:
            flash("Faça login para acessar o gerador de planejamento.")
            return redirect(url_for("login"))

        config_file = request.files.get("config_file")
        grade_file = request.files.get("grade_file")
        escopo_files = request.files.getlist("escopo_files")

        if not config_file or config_file.filename == "":
            flash("Envie o arquivo config.json para gerar o planejamento.")
            return redirect(request.url)

        if not allowed_file(config_file.filename) or not config_file.filename.lower().endswith(".json"):
            flash("O arquivo de configuração deve ser um JSON válido.")
            return redirect(request.url)

        all_files = {}
        if grade_file and grade_file.filename:
            all_files[secure_filename(grade_file.filename)] = grade_file

        for uploaded in escopo_files:
            if uploaded and uploaded.filename:
                all_files[secure_filename(uploaded.filename)] = uploaded

        if grade_file and grade_file.filename and not allowed_file(grade_file.filename):
            flash("O arquivo da grade deve ser um arquivo .xlsx.")
            return redirect(request.url)

        for uploaded in escopo_files:
            if uploaded and uploaded.filename and not allowed_file(uploaded.filename):
                flash("Os arquivos de escopo devem ser arquivos .xlsx.")
                return redirect(request.url)

        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        config_path = temp_path / "config.json"
        config_content = config_file.read()
        config_path.write_bytes(config_content)

        try:
            config_data = json.loads(config_content)
        except json.JSONDecodeError:
            shutil.rmtree(temp_dir, ignore_errors=True)
            flash("O arquivo config.json está inválido ou mal formatado.")
            return redirect(request.url)

        grade_upload = None
        if grade_file and grade_file.filename:
            grade_upload = grade_file

        uploaded_files = {name: file for name, file in all_files.items()}

        if not grade_upload:
            grade_upload = find_uploaded_file(uploaded_files, config_data.get("grade_horaria", ""))

        if not grade_upload:
            shutil.rmtree(temp_dir, ignore_errors=True)
            flash("Não foi possível localizar o arquivo de grade. Faça upload do arquivo de grade ou verifique o nome no config.json.")
            return redirect(request.url)

        grade_path = temp_path / normalize_file_name(grade_upload.filename)
        grade_upload.save(grade_path)
        config_data["grade_horaria"] = str(grade_path)

        escopo_paths = []
        for item in config_data.get("arquivos_escopo", []):
            arquivo_ref = item.get("arquivo")
            if not arquivo_ref:
                continue

            upload = find_uploaded_file(uploaded_files, arquivo_ref)
            if upload is None:
                shutil.rmtree(temp_dir, ignore_errors=True)
                flash(
                    f"Não foi possível localizar o arquivo de escopo {arquivo_ref}. Faça upload do arquivo correspondente."
                )
                return redirect(request.url)

            path = temp_path / normalize_file_name(upload.filename)
            upload.save(path)
            item["arquivo"] = str(path)
            escopo_paths.append(path)

        output_path = temp_path / "base_maladireta.xlsx"

        try:
            generated_path = generate_planning_from_dict(
                config_data,
                output_path=str(output_path),
                save_config=False,
            )
        except Exception as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            flash(f"Erro ao gerar o planejamento: {exc}")
            return redirect(request.url)

        @after_this_request
        def cleanup(response):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
            return response

        return send_file(
            generated_path,
            as_attachment=True,
            download_name="base_maladireta.xlsx",
        )

    return render_template("index.html", user=session.get("user"))


@app.route("/login")
def login():
    if not oauth_configured():
        flash("Google OAuth não está configurado. Defina GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET.")
        return redirect(url_for("index"))

    redirect_uri = url_for("authorize", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    error = request.args.get("error")
    if error:
        flash(f"Falha na autorização Google: {error}")
        return redirect(url_for("index"))

    if not oauth_configured():
        flash("Google OAuth não está configurado. Defina GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET.")
        return redirect(url_for("index"))

    try:
        token = oauth.google.authorize_access_token()
    except Exception as exc:
        app.logger.exception("Erro durante authorize_access_token")
        flash("Erro ao completar o login com o Google. Verifique as credenciais e o URI de redirecionamento OAuth.")
        return redirect(url_for("index"))

    if not token or "access_token" not in token:
        app.logger.error("authorize_access_token retornou token inválido: %s", token)
        flash("Não foi possível obter o token de acesso do Google.")
        return redirect(url_for("index"))

    try:
        user_response = oauth.google.get("userinfo")
        user_info = user_response.json()
    except Exception as exc:
        app.logger.exception("Erro ao buscar userinfo do Google")
        flash("Não foi possível buscar os dados do usuário no Google.")
        return redirect(url_for("index"))

    if user_response.status_code != 200:
        app.logger.error("Google userinfo returned %s: %s", user_response.status_code, user_response.text)
        flash(f"Erro ao buscar os dados do usuário no Google (status {user_response.status_code}).")
        return redirect(url_for("index"))

    if not user_info:
        flash("Não foi possível obter informações do usuário Google.")
        return redirect(url_for("index"))

    session["user"] = user_info
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

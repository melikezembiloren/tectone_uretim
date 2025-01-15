from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime
from io import BytesIO
from openpyxl import Workbook
from google.cloud import firestore

# Firestore istemcisi
service_account_path = r"C:\Users\melike.zembiloren\Desktop\uretim_app\serviceAccountKey.json"
db = firestore.Client.from_service_account_json(service_account_path)

app = Flask(__name__)

@app.route("/uretim/hata", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Yeni hata kaydı ekle
        hata = request.form.get("hata")
        son_haneler = request.form.get("son_haneler")
        aciklama = request.form.get("aciklama")
        tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        seri_numara = f"TLA{son_haneler}"

        db.collection("hata_kayitlari").add({
            "seri_numara": seri_numara,
            "hata": hata,
            "tarih": tarih,
            "aciklama": aciklama
        })

        return redirect(url_for("index"))

    # Filtreleme parametrelerini al
    filtreli_tarih = request.args.get("tarih")
    filtreli_hata = request.args.get("hata")

    # Firestore sorgusunu oluştur
    query = db.collection("hata_kayitlari")
    if filtreli_tarih:
        query = query.where("tarih", ">=", filtreli_tarih)
    if filtreli_hata:
        query = query.where("hata", "==", filtreli_hata)

    # Veritabanından verileri al
    seriler = [doc.to_dict() | {"id": doc.id} for doc in query.stream()]
    return render_template(
        "index.html", 
        seriler=seriler,
        hata_listesi=["Sinyal Yok", "Ekran Hatası", "Panel Kırık", "Diğer"],
        aciklama_listesi=["LVDS kablosu değişti", "Anakart değiştirildi", "Güç kaynağı değiştirildi", "Diğer"]
    )

@app.route("/delete/<doc_id>", methods=["GET"])
def delete(doc_id):
    try:
        db.collection("hata_kayitlari").document(doc_id).delete()
        return redirect(url_for("index"))
    except Exception as e:
        return f"Hata oluştu: {str(e)}", 500

@app.route('/download', methods=['POST'])
def download():
    # Firestore'dan verileri al
    docs = db.collection("hata_kayitlari").stream()
    rows = [doc.to_dict() for doc in docs]

    # Excel dosyası oluştur
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Hata Listesi"

    # Başlıkları ekle
    headers = ["Seri Numarası", "Hata", "Tarih", "Açıklama"]
    sheet.append(headers)

    for row in rows:
        sheet.append([row.get("seri_numara"), row.get("hata"), row.get("tarih"), row.get("aciklama")])

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="hata_listesi.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

from pathlib import Path
import os
import sys
import tempfile

from flask import Flask, render_template, request
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

PROJECT_ROOT = Path(__file__).resolve().parent
for import_root in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tif", "tiff", "webp"}

CLASS_LABELS_AR = {
    "Cyst": "كيس",
    "Normal": "طبيعي",
    "Stone": "حصوة",
    "Tumor": "ورم",
}

# Lazy initialization: load the model once, on the first prediction request.
_predictor = None


def get_predictor():
    global _predictor

    if _predictor is None:
        from cnnClassifier.pipeline.prediction import KidneyImagePredictor
        _predictor = KidneyImagePredictor()

    return _predictor


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    uploaded_name = None

    if request.method == "POST":
        upload = request.files.get("image")

        if upload is None or not upload.filename:
            error = "اختر صورة أولًا."
        elif not allowed_file(upload.filename):
            error = "صيغة الصورة غير مدعومة. استخدم JPG أو PNG أو WEBP أو TIFF أو BMP."
        else:
            safe_name = secure_filename(upload.filename)
            suffix = Path(safe_name).suffix.lower()

            if not suffix:
                error = "اسم الملف لا يحتوي على امتداد صورة صالح."
            else:
                temp_path = None

                try:
                    # Use a temporary file, and delete it after prediction.
                    with tempfile.NamedTemporaryFile(
                        prefix="kidney_upload_",
                        suffix=suffix,
                        delete=False,
                    ) as temp_file:
                        temp_path = Path(temp_file.name)
                        upload.save(temp_file)

                    # Validate that this is a readable image with reasonable dimensions.
                    with Image.open(str(temp_path)) as check_image:
                        width, height = check_image.size

                        if width < 32 or height < 32:
                            raise ValueError("أبعاد الصورة صغيرة جدًا.")
                        if width * height > 40_000_000:
                            raise ValueError("أبعاد الصورة كبيرة جدًا للمعالجة الآمنة.")

                        check_image.verify()

                    prediction = get_predictor().predict_image(temp_path)

                    result = {
                        **prediction,
                        "predicted_class_ar": CLASS_LABELS_AR.get(
                            prediction["predicted_class"],
                            prediction["predicted_class"],
                        ),
                        "filename": safe_name,
                        "probabilities_ar": [
                            {
                                "name": name,
                                "name_ar": CLASS_LABELS_AR.get(name, name),
                                "probability": probability,
                                "percent": round(probability * 100.0, 2),
                            }
                            for name, probability in prediction[
                                "class_probabilities"
                            ].items()
                        ],
                    }
                    uploaded_name = safe_name

                except (
                    UnidentifiedImageError,
                    OSError,
                    ValueError,
                    FileNotFoundError,
                ) as exc:
                    app.logger.info("Image could not be processed: %s", exc)
                    error = (
                        "تعذرت معالجة الصورة. تأكد أنها صورة سليمة "
                        "وبصيغة مدعومة."
                    )
                except Exception:
                    app.logger.exception("Prediction request failed")
                    error = (
                        "حدث خطأ أثناء تشغيل النموذج. راجع سجل الخادم "
                        "للتعرف على السبب."
                    )
                finally:
                    if temp_path is not None:
                        try:
                            temp_path.unlink(missing_ok=True)
                        except OSError:
                            app.logger.warning("Could not remove temporary upload.")

    return render_template(
        "index.html",
        result=result,
        error=error,
        uploaded_name=uploaded_name,
    )


@app.errorhandler(413)
def file_too_large(_error):
    return render_template(
        "index.html",
        error="حجم الصورة أكبر من الحد المسموح (10 ميغابايت).",
        result=None,
        uploaded_name=None,
    ), 413


if __name__ == "__main__":
    # Local-only development server; debug mode is disabled.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)

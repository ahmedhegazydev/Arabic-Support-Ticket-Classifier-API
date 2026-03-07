from app.models.loader import model_loader


def get_classifier():
    return model_loader.load_classifier()
import importlib
import pkgutil

import app.models
import app.models.associations
from app.db.database import Base, engine

for module_info in pkgutil.iter_modules(app.models.__path__, app.models.__name__ + "."):
    _ = importlib.import_module(module_info.name)

for module_info in pkgutil.iter_modules(
    app.models.associations.__path__, app.models.associations.__name__ + "."
):
    _ = importlib.import_module(module_info.name)


Base.metadata.create_all(bind=engine)

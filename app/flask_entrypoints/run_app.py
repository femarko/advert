import app.orm.table_mapper, app.domain
from app.flask_entrypoints import adv

if __name__ == "__main__":
    app.orm.table_mapper.start_mapping()
    adv.run(debug=True)

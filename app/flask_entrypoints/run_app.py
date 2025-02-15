import app.orm.table_mapper
from app.flask_entrypoints import adv, views

if __name__ == "__main__":
    app.orm.table_mapper.start_mapping()

    adv.run(debug=True)

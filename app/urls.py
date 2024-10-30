from app import adv
from app.views import AdvView

adv_view = AdvView.as_view("adv_view")
adv.add_url_rule("/adv/<int:adv_id>", view_func=adv_view, methods=["GET", "PATCH", "DELETE"])
adv.add_url_rule("/adv", view_func=adv_view, methods=["POST"])


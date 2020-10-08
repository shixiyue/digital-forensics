import django_tables2 as tables
from django_tables2.utils import A

from models import Submission

class SubmissionTable(tables.Table):
    id = tables.Column(verbose_name="Submission ID")
    submission_time = tables.DateTimeColumn(format="Y-m-d", verbose_name="Date")
    num_of_images = tables.Column(
        accessor=A("num_of_images"), verbose_name="Number of Images"
    )
    links = tables.LinkColumn(
        "submission_details",
        verbose_name="Analysis and Certificates",
        text="Details",
        args=[A("pk")],
        attrs={"a": {"style": "color: #0275d8;"}},
    )
    template = """
        <div class="dropleft">
            <button class="btn btn-sm btn-primary dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"></button>
            <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                {% if record.status == 4 %}
                <a class="dropdown-item" href="#">Appeal</a>
                {% elif record.status == 0 %}
                <a class="dropdown-item" href="#">Request Certificates</a>
                {% endif %}
                <a class="dropdown-item" href="#">Contact Support</a>
            </div>
        </div>
    """
    actions = tables.TemplateColumn(template)

    class Meta:
        model = Submission
        template_name = "django_tables2/bootstrap4.html"
        fields = ("id", "submission_time", "status")
        sequence = (
            "id",
            "submission_time",
            "status",
            "num_of_images",
            "links",
            "actions",
        )
        attrs = {"style": "background-color: #ffffff;"}

class SubmissionAdminTable(tables.Table):
    id = tables.Column(verbose_name="Submission ID")
    submission_time = tables.DateTimeColumn(format="Y-m-d", verbose_name="Date")
    num_of_images = tables.Column(
        accessor=A("num_of_images"), verbose_name="Number of Images"
    )
    links = tables.LinkColumn(
        "submission_admin",
        verbose_name="Analysis and Certificates",
        text="Details",
        args=[A("pk")],
        attrs={"a": {"style": "color: #0275d8;"}},
    )
    email = tables.Column(
        accessor=A("email"), verbose_name="User Email"
    )
    admin_email = tables.Column(
        accessor=A("admin_email"), verbose_name="Last Admin Processed"
    )

    class Meta:
        model = Submission
        template_name = "django_tables2/bootstrap4.html"
        fields = ("id", "submission_time", "status")
        sequence = (
            "id",
            "submission_time",
            "email",
            "status",
            "num_of_images",
            "admin_email",
            "links",
        )
        attrs = {"style": "background-color: #ffffff;"}
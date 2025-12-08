from odoo import fields, models


class CustomerProject(models.Model):
    _name = "ife.customer.project"
    _description = "Customer Project"

    name = fields.Char(required=True)
    github_url = fields.Char(required=True)
    environment_ids = fields.One2many("ife.environment", "customer_project_id")

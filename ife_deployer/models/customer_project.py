from odoo import fields, models


class CustomerProject(models.Model):
    _name = "ife.customer.project"
    _description = "Customer Project"

    name = fields.Char(required=True)
    config_repo_id = fields.Many2one(
        "ife.repo",
        string="Config Repository",
        required=True,
        domain=[("type", "=", "config")],
        copy=False,
    )
    project_repo_id = fields.Many2one(
        "ife.repo",
        string="Project Repository",
        required=True,
        domain=[("type", "=", "project")],
        copy=False,
    )
    environment_ids = fields.One2many(
        "ife.environment", "customer_project_id", copy=False
    )

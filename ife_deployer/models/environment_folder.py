from odoo import fields, models


class EnvironmentFolder(models.Model):
    _name = "ife.environment.folder"
    _description = "Folder Name"

    name = fields.Char(string="Folder", required=True)
    repo_id = fields.Many2one(
        "ife.repo", string="Repository", required=True, domain=[("type", "=", "module")]
    )
    ref = fields.Char(string="Reference", required=True)
    environment_id = fields.Many2one("ife.environment", required=True, copy=False)
    customer_project_id = fields.Many2one(
        "ife.customer.project", related="environment_id.customer_project_id"
    )
    module_ids = fields.One2many("ife.environment.module", "folder_id")

    _sql_constraints = [
        (
            "folder_env_unique",
            "unique(name, environment_id)",
            "Folder name must be unique per environment!",
        ),
    ]

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.environment_id.name} - {rec.name}"

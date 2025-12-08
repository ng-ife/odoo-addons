from odoo import fields, models


class Module(models.Model):
    _name = "ife.module"
    _description = "Module"

    name = fields.Char(required=True)
    folder_id = fields.Many2one("ife.foldername", required=True)
    environment_ids = fields.Many2many("ife.environment")

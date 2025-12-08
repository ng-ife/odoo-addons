from odoo import fields, models


class FolderName(models.Model):
    _name = "ife.foldername"
    _description = "Folder Name"

    name = fields.Char(string="Folder", required=True)
    github_url = fields.Char(string="GitHub URL")

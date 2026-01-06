from odoo import fields, models


class Library(models.Model):
    _name = "module.library"
    _description = "Modul Bibliothek"

    name = fields.Char(required=True)
    description = fields.Text()

    repository_ids = fields.One2many("git.repository", "library_id")

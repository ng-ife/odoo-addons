from odoo import fields, models


class ModuleLibraryModule(models.Model):
    _name = "module.library.module"
    _description = "Gefundene Odoo Module"
    _order = "name"

    name = fields.Char(string="Modul Name", required=True)
    technical_name = fields.Char(required=True)
    summary = fields.Char()
    version = fields.Char()
    author = fields.Char()

    repository_id = fields.Many2one("git.repository", ondelete="cascade", required=True)
    library_id = fields.Many2one(
        related="repository_id.library_id",
        store=True,
        readonly=True,
    )

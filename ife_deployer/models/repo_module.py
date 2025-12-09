from odoo import models, fields

class RepoModule(models.Model):
    _name = 'ife.repo.module'
    _description = 'Repository Module Template'

    name = fields.Char(required=True)
    repo_id = fields.Many2one('ife.repo', string='Repository', required=True, domain="[('type', '=', 'module')]")

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EnvironmentModule(models.Model):
    _name = 'ife.environment.module'
    _description = 'Environment Module'

    name = fields.Char(compute='_compute_name', store=True)
    folder_id = fields.Many2one('ife.environment.folder', required=True)
    folder_repo_id = fields.Many2one('ife.repo', string='Folder Repository', related='folder_id.repo_id')
    repo_module_id = fields.Many2one('ife.repo.module', string='Repo Module', required=True, domain="[('repo_id', '=', folder_repo_id)]")
    environment_id = fields.Many2one('ife.environment', string='Environment', related='folder_id.environment_id')

    _sql_constraints = [
        ('unique_name_folder', 'unique(name, folder_id)', 'The combination of module name and folder must be unique!'),
    ]
    
    @api.constrains('folder_id', 'repo_module_id')
    def _check_folder_repo_match(self):
        for rec in self:
            if rec.folder_id.repo_id != rec.repo_module_id.repo_id:
                raise ValidationError('The folder and module must belong to the same repository!')

    @api.depends('repo_module_id')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.repo_module_id.name or ''

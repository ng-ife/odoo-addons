from odoo import api, models, fields

class EnvironmentFolder(models.Model):

    _name = 'ife.environment.folder'
    _description = 'Folder Name'

    name = fields.Char(string="Folder", required=True)
    display_name = fields.Char(string="Display Name", compute="_compute_display_name", store=True)
    repo_id = fields.Many2one('ife.repo', string='Repository', required=True, domain=[('type', '=', 'module')])
    ref = fields.Char(string="Reference", required=True)
    environment_id = fields.Many2one('ife.environment', required=True)
    customer_project_id = fields.Many2one('ife.customer.project', related='environment_id.customer_project_id')
    module_ids = fields.One2many('ife.environment.module', 'folder_id')

    _sql_constraints = [
        ('folder_env_unique', 'unique(name, environment_id)', 'Folder name must be unique per environment!'),
    ]

    @api.depends('environment_id.name', 'name')
    def _compute_display_name(self):
        for rec in self:
            env_name = rec.environment_id.name or ''
            folder_name = rec.name or ''
            rec.display_name = f"{env_name} - {folder_name}" if env_name and folder_name else env_name or folder_name

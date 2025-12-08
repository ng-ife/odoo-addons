from odoo import models, fields

class Environment(models.Model):
    _name = 'ife.environment'
    _description = 'Environment'

    name = fields.Char(required=True)
    branch = fields.Char(required=True)
    module_ids = fields.Many2many('ife.module')

    customer_project_id = fields.Many2one('ife.customer.project', required=True)
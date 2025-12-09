from odoo import fields, models
from ruamel.yaml import YAML
import os

class Environment(models.Model):
    _name = "ife.environment"
    _description = "Environment"

    name = fields.Char(required=True)
    folder_ids = fields.One2many('ife.environment.folder', 'environment_id')
    module_ids = fields.One2many('ife.environment.module', 'environment_id')
    customer_project_id = fields.Many2one("ife.customer.project", required=True)
    repo_id = fields.Many2one('ife.repo', related='customer_project_id.config_repo_id')
    branch_id = fields.Many2one('ife.repo.branch', required=True, domain="[('repo_id', '=', repo_id)]")
    
    def export_config_yaml(self):
        self.ensure_one()
        repos = {}
        addons = {}
        for folder in self.folder_ids:
            repo = folder.repo_id
            if not repo:
                continue
            repo_key = f"./{folder.name}"
            repos[repo_key] = {
                'defaults': {'depth': 1},
                'remotes': {'origin': repo.github_url},
                'merges': [f"origin {folder.ref}"],
            }
            modules = [mod.name for mod in folder.module_ids]
            if modules:
                addons[repo_key] = modules
        self.branch_id.checkout()
        base_path = self.repo_id.full_path
        repo_path = os.path.join(base_path, 'repos.yaml')
        addons_path = os.path.join(base_path, 'addons.yaml')
        yaml = YAML()
        yaml.preserve_quotes = True 
        yaml.width = 1000
        yaml.indent(mapping=2, sequence=4, offset=2)
        with open(repo_path, 'w') as f:
            yaml.dump(repos, f)
        with open(addons_path, 'w') as f:
            yaml.dump(addons, f)
        return True

    # Todo add, commit and push taken from branch
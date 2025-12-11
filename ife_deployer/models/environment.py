import io

from ruamel.yaml import YAML

from odoo import fields, models

ENVIRONEMENT_TYPES = [
    ("dev", "Development"),
    ("stage", "Staging"),
    ("prod", "Production"),
]


class Environment(models.Model):
    _name = "ife.environment"
    _description = "Environment"

    name = fields.Char(required=True)
    folder_ids = fields.One2many("ife.environment.folder", "environment_id")
    module_ids = fields.One2many("ife.environment.module", "environment_id")
    customer_project_id = fields.Many2one("ife.customer.project", required=True)
    repo_id = fields.Many2one("ife.repo", related="customer_project_id.config_repo_id")
    branch_id = fields.Many2one(
        "ife.repo.branch", required=True, domain="[('repo_id', '=', repo_id)]"
    )
    type = fields.Selection(
        ENVIRONEMENT_TYPES, string="Environment Type", required=True
    )
    is_dirty = fields.Boolean(related="repo_id.is_dirty")
    addons_yaml = fields.Text(string="Addons YAML")
    repos_yaml = fields.Text(string="Repos YAML")

    def _get_yaml_field_value(self, data_dict):
        self.ensure_one()
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.width = 1000
        yaml.indent(mapping=2, sequence=4, offset=2)
        stream = io.StringIO()
        yaml.dump(data_dict, stream)
        return stream.getvalue()

    def action_fetch_config_yamls(self):
        self.ensure_one()
        self.branch_id.action_pull_branch()
        self.repos_yaml = self.branch_id.read_file("repos.yaml")
        self.addons_yaml = self.branch_id.read_file("addons.yaml")
        self.generate_fields_from_yaml()
        return True

    def generate_fields_from_yaml(self):
        self.ensure_one()
        yaml = YAML()
        yaml.preserve_quotes = True

        # --- Folders and Repos ---
        if self.repos_yaml:
            repos_data = yaml.load(self.repos_yaml)
            for repo_folder, repo_info in repos_data.items():
                # Find or create folder
                repo_folder = repo_folder.lstrip("./")
                folder = self.folder_ids.filtered(lambda f: f.name == repo_folder)
                if not folder:
                    # Find or create repo
                    repo_remote = repo_info.get("remotes", {})
                    repo_key, repo_url = next(iter(repo_remote.items()), None)

                    repo = self.env["ife.repo"].search(
                        [("github_url", "=", repo_url)], limit=1
                    )
                    if not repo and repo_url:
                        repo = self.env["ife.repo"].create(
                            {
                                "github_url": repo_url,
                                "type": "module",
                                "name": repo_folder,
                                "path": repo_folder,
                            }
                        )
                    folder = self.env["ife.environment.folder"].create(
                        {
                            "name": repo_folder,
                            "repo_id": repo.id if repo else False,
                            "ref": repo_info.get("merges", ["origin main"])[0].split(
                                " ", 1
                            )[1]
                            if repo_info.get("merges")
                            else "main",
                            "environment_id": self.id,
                            "customer_project_id": self.customer_project_id.id,
                        }
                    )
                else:
                    folder = folder[0]
                    ref_list = repo_info.get("merges", [])
                    if ref_list:
                        folder.ref = ref_list[0].split(" ", 1)[1]

        # --- Modules ---
        if self.addons_yaml:
            addons_data = yaml.load(self.addons_yaml)
            for repo_key, module_names in addons_data.items():
                folder = self.folder_ids.filtered(lambda f: f.name == repo_key)
                if not folder:
                    # If folder missing, create it (repo creation handled above)
                    repo = self.env["ife.repo"].search(
                        [("name", "=", repo_key)], limit=1
                    )
                    folder = self.env["ife.environment.folder"].create(
                        {
                            "name": repo_key,
                            "repo_id": repo.id if repo else False,
                            "ref": "main",
                            "environment_id": self.id,
                            "customer_project_id": self.customer_project_id.id,
                        }
                    )
                else:
                    folder = folder[0]

                # For each module, ensure repo module and environment module exist
                repo = folder.repo_id
                for mod_name in module_names:
                    # Find or create repo module
                    repo_module = self.env["ife.repo.module"].search(
                        [("repo_id", "=", repo.id), ("name", "=", mod_name)], limit=1
                    )
                    if not repo_module:
                        repo_module = self.env["ife.repo.module"].create(
                            {"repo_id": repo.id, "name": mod_name}
                        )
                    # Find or create environment module
                    env_module = self.env["ife.environment.module"].search(
                        [
                            ("environment_id", "=", self.id),
                            ("folder_id", "=", folder.id),
                            ("repo_module_id", "=", repo_module.id),
                        ],
                        limit=1,
                    )
                    if not env_module:
                        env_module = self.env["ife.environment.module"].create(
                            {
                                "folder_id": folder.id,
                                "repo_module_id": repo_module.id,
                            }
                        )
                    # Link module to folder
                    if env_module not in folder.module_ids:
                        folder.module_ids += env_module
        return True

    def generate_config_yaml(self):
        self.ensure_one()
        repos = {}
        addons = {}
        for folder in self.folder_ids:
            repo = folder.repo_id
            if not repo:
                continue
            repo_key = folder.name
            repos[f"./{repo_key}"] = {
                "defaults": {"depth": 1},
                "remotes": {"origin": repo.github_url},
                "merges": [f"origin {folder.ref}"],
            }
            modules = [mod.name for mod in folder.module_ids]
            if modules:
                addons[repo_key] = modules
        self.repos_yaml = self._get_yaml_field_value(repos)
        self.addons_yaml = self._get_yaml_field_value(addons)
        return True

    def action_commit_config_yamls(self):
        self.ensure_one()
        self.branch_id.checkout()
        self.branch_id.write_file("repos.yaml", self.repos_yaml)
        self.branch_id.write_file("addons.yaml", self.addons_yaml)
        self.branch_id.action_commit_and_push_branch()
        return True

    def action_clean_repo(self):
        self.ensure_one()
        self.repo_id.action_clean()
        return True

    def action_copy_production_config(self):
        self.ensure_one()
        prod_env = self.customer_project_id.environment_ids.filtered(
            lambda e: e.type == "prod"
        )
        if not prod_env:
            return False
        prod_env = prod_env[0]
        self.repos_yaml = prod_env.repos_yaml
        self.addons_yaml = prod_env.addons_yaml
        self.generate_fields_from_yaml()
        return True
